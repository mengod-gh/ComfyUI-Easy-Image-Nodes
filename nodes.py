from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path, PurePosixPath, PureWindowsPath

import numpy as np
import torch
from PIL import Image, ImageOps, ImageSequence
from PIL.PngImagePlugin import PngInfo

import comfy.model_management
import folder_paths
from comfy.cli_args import args


CATEGORY = "Easy Image Nodes"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
SAVE_FORMATS = {"png": ".png", "jpg": ".jpg", "webp": ".webp"}
SAVE_EXTENSIONS = set(SAVE_FORMATS.values())
STRIPPED_SAVE_EXTENSIONS = SAVE_EXTENSIONS | {".jpeg"}
SORT_ORDERS = ("ascending", "descending")
DATE_TOKEN_RE = re.compile(r"%date:([^%]+)%")
FORMAT_TOKEN_RE = re.compile(r"%([^%]+)%")

_requeued_runs: set[tuple[int, str, int]] = set()


def _as_input_path(relative_path: str) -> Path:
    path = _clean_relative_path(relative_path, "input path")
    base = Path(folder_paths.get_input_directory()).resolve()
    full_path = (base / path).resolve()
    if os.path.commonpath((str(base), str(full_path))) != str(base):
        raise RuntimeError(f"Input path escapes the ComfyUI input directory: {relative_path}")
    return full_path


def _clean_relative_path(value: str, label: str) -> str:
    value = str(value or "").strip().replace("\\", "/")
    if not value:
        raise RuntimeError(f"{label} is empty.")

    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if posix.is_absolute() or windows.is_absolute() or windows.drive:
        raise RuntimeError(f"{label} must be relative to the ComfyUI directory it belongs to: {value}")

    parts = [part for part in posix.parts if part not in ("", ".")]
    if any(part == ".." for part in parts):
        raise RuntimeError(f"{label} cannot contain '..': {value}")
    if not parts:
        raise RuntimeError(f"{label} is empty.")
    return "/".join(parts)


def _clean_optional_output_folder(value: str) -> str:
    value = str(value or "").strip().replace("\\", "/")
    if not value:
        return ""

    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if posix.is_absolute() or windows.is_absolute() or windows.drive:
        raise RuntimeError(f"Output folder must be relative to the ComfyUI output directory: {value}")

    parts = [part for part in posix.parts if part not in ("", ".")]
    if any(part == ".." for part in parts):
        raise RuntimeError(f"Output folder cannot contain '..': {value}")
    return "/".join(parts)


def _path_metadata(relative_path: str) -> tuple[str, str, str, str]:
    clean_path = _clean_relative_path(relative_path, "image path")
    name = PurePosixPath(clean_path).name
    suffix = PurePosixPath(clean_path).suffix
    stem = name[: -len(suffix)] if suffix else name
    return name, stem, suffix.lower(), clean_path


def _normalize_save_format(extension: str) -> str:
    value = str(extension or "").strip().lower().lstrip(".")
    if value == "jpeg":
        value = "jpg"
    if value not in SAVE_FORMATS:
        raise RuntimeError(f"Unsupported output extension: {extension}")
    return value


def _normalize_sort_order(sort_order: str) -> str:
    value = str(sort_order or "ascending").strip().lower()
    if value not in SORT_ORDERS:
        raise RuntimeError(f"Unsupported sort order: {sort_order}")
    return value


def _is_linked_prompt_input(prompt, unique_id, input_name: str) -> bool:
    if prompt is None or unique_id is None or not isinstance(prompt, dict):
        return False

    node = prompt.get(str(unique_id))
    if node is None:
        node = prompt.get(unique_id)
    if not isinstance(node, dict):
        return False

    inputs = node.get("inputs", {})
    if not isinstance(inputs, dict):
        return False

    value = inputs.get(input_name)
    return isinstance(value, (list, tuple)) and len(value) == 2


def _normalize_token_name(value) -> str:
    return re.sub(r"\s+", "", str(value or "")).casefold()


def _prompt_node_labels(node_id, node: dict) -> set[str]:
    labels = {_normalize_token_name(node_id)}

    class_type = node.get("class_type")
    if class_type:
        labels.add(_normalize_token_name(class_type))

    meta = node.get("_meta")
    if isinstance(meta, dict) and meta.get("title"):
        labels.add(_normalize_token_name(meta["title"]))

    return labels


def _prompt_input_value(prompt, node_name: str, input_name: str):
    if not isinstance(prompt, dict):
        return None

    target_node = _normalize_token_name(node_name)
    target_input = _normalize_token_name(input_name)
    for node_id, node in prompt.items():
        if not isinstance(node, dict):
            continue
        if target_node not in _prompt_node_labels(node_id, node):
            continue

        inputs = node.get("inputs", {})
        if not isinstance(inputs, dict):
            continue
        for key, value in inputs.items():
            if _normalize_token_name(key) != target_input:
                continue
            if isinstance(value, (list, tuple)) and len(value) == 2:
                return None
            return value
    return None


def _format_prompt_value(value) -> str:
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, ensure_ascii=False)


def _comfy_date_to_strftime(date_format: str) -> str:
    replacements = (
        ("yyyy", "%Y"),
        ("yy", "%y"),
        ("MM", "%m"),
        ("dd", "%d"),
        ("HH", "%H"),
        ("hh", "%H"),
        ("mm", "%M"),
        ("ss", "%S"),
    )
    output = date_format
    for source, target in replacements:
        output = output.replace(source, target)
    return output


def _expand_filename_format(value: str, image_width: int, image_height: int, prompt=None) -> str:
    def replace_date(match: re.Match) -> str:
        return time.strftime(_comfy_date_to_strftime(match.group(1)), time.localtime())

    value = DATE_TOKEN_RE.sub(replace_date, str(value or ""))
    builtin_values = {
        "width": str(image_width),
        "height": str(image_height),
        "year": str(time.localtime().tm_year),
        "month": str(time.localtime().tm_mon).zfill(2),
        "day": str(time.localtime().tm_mday).zfill(2),
        "hour": str(time.localtime().tm_hour).zfill(2),
        "minute": str(time.localtime().tm_min).zfill(2),
        "second": str(time.localtime().tm_sec).zfill(2),
    }

    def replace_token(match: re.Match) -> str:
        token = match.group(1)
        normalized = _normalize_token_name(token)
        if normalized in builtin_values:
            return builtin_values[normalized]

        if "." in token:
            node_name, input_name = token.rsplit(".", 1)
            value = _prompt_input_value(prompt, node_name, input_name)
            if value is not None:
                return _format_prompt_value(value)
        return match.group(0)

    return FORMAT_TOKEN_RE.sub(replace_token, value)


def _clean_optional_filename_prefix(value: str, image_width: int, image_height: int, prompt=None) -> str:
    value = _expand_filename_format(value, image_width, image_height, prompt)
    value = str(value or "").strip().replace("\\", "/")
    if not value:
        return ""

    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if posix.is_absolute() or windows.is_absolute() or windows.drive:
        raise RuntimeError(f"Filename prefix must be relative to the ComfyUI output directory: {value}")

    parts = [part for part in posix.parts if part not in ("", ".")]
    if any(part == ".." for part in parts):
        raise RuntimeError(f"Filename prefix cannot contain '..': {value}")
    return "/".join(parts)


def _next_auto_counter(output_folder: Path, stem: str, suffix: str) -> int:
    if stem:
        pattern = re.compile(rf"^{re.escape(stem)}_(\d+){re.escape(suffix)}$", re.IGNORECASE)
    else:
        pattern = re.compile(rf"^(\d+){re.escape(suffix)}$", re.IGNORECASE)

    highest = 0
    if output_folder.is_dir():
        for path in output_folder.iterdir():
            if not path.is_file():
                continue
            match = pattern.match(path.name)
            if match:
                highest = max(highest, int(match.group(1)))
    return highest + 1


def _auto_increment_relative_path(
    filename_prefix: str,
    extension: str,
    output_dir: Path,
    image_width: int,
    image_height: int,
    prompt=None,
) -> str:
    suffix = SAVE_FORMATS[_normalize_save_format(extension)]
    clean_prefix = _clean_optional_filename_prefix(filename_prefix, image_width, image_height, prompt)

    subfolder = ""
    stem = ""
    if clean_prefix:
        prefix_path = PurePosixPath(clean_prefix)
        if str(prefix_path.parent) != ".":
            subfolder = prefix_path.parent.as_posix()
        stem = prefix_path.name
        if PurePosixPath(stem).suffix.lower() in STRIPPED_SAVE_EXTENSIONS:
            stem = stem[: -len(PurePosixPath(stem).suffix)]

    target_folder = (output_dir / subfolder).resolve()
    if os.path.commonpath((str(output_dir), str(target_folder))) != str(output_dir):
        raise RuntimeError(f"Output path escapes the ComfyUI output directory: {clean_prefix}")

    counter = _next_auto_counter(target_folder, stem, suffix)
    while True:
        filename = f"{stem}_{counter:04d}{suffix}" if stem else f"{counter:04d}{suffix}"
        candidate = target_folder / filename
        if not candidate.exists():
            break
        counter += 1

    if subfolder:
        return f"{subfolder}/{filename}"
    return filename


def _replace_path_extension(relative_path: str, extension: str) -> str:
    suffix = SAVE_FORMATS[_normalize_save_format(extension)]
    path = PurePosixPath(_clean_relative_path(relative_path, "filename"))
    if path.suffix:
        path = path.with_suffix(suffix)
    else:
        path = PurePosixPath(f"{path.as_posix()}{suffix}")
    return path.as_posix()


def _list_input_images(folder: str, sort_order: str = "ascending") -> list[str]:
    folder = _clean_relative_path(folder, "folder")
    root = _as_input_path(folder)
    if not root.is_dir():
        raise RuntimeError(f"Folder does not exist under ComfyUI input: {folder}")

    files: list[str] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            files.append(path.relative_to(root).as_posix())
    files.sort(key=lambda item: item.casefold(), reverse=_normalize_sort_order(sort_order) == "descending")
    if not files:
        raise RuntimeError(f"No supported images found in input folder: {folder}")
    return files


def _load_image_tensor(path: Path) -> tuple[torch.Tensor, torch.Tensor]:
    dtype = comfy.model_management.intermediate_dtype()
    device = comfy.model_management.intermediate_device()

    img = Image.open(path)
    output_images = []
    output_masks = []
    width = height = None

    for frame in ImageSequence.Iterator(img):
        frame = ImageOps.exif_transpose(frame)
        rgba = frame.convert("RGBA")

        if width is None or height is None:
            width, height = rgba.size
        if rgba.size != (width, height):
            continue

        arr = np.asarray(rgba).astype(np.float32) / 255.0
        rgb = torch.from_numpy(arr[..., :3])[None,]
        alpha_mask = 1.0 - torch.from_numpy(arr[..., 3])[None,]
        output_images.append(rgb.to(dtype=dtype))
        output_masks.append(alpha_mask.to(dtype=dtype))

    if not output_images:
        raise RuntimeError(f"No loadable image frames found: {path}")

    image = torch.cat(output_images, dim=0).to(device=device, dtype=dtype)
    mask = torch.cat(output_masks, dim=0).to(device=device, dtype=dtype)
    return image, mask


def _hash_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _resize_mask(mask: torch.Tensor, width: int, height: int) -> torch.Tensor:
    if mask.ndim == 3:
        mask = mask[0]
    mask = mask.detach().cpu().float().clamp(0, 1)
    if mask.shape[-2:] == (height, width):
        return mask

    mask = torch.nn.functional.interpolate(
        mask.unsqueeze(0).unsqueeze(0),
        size=(height, width),
        mode="bilinear",
        align_corners=False,
    )
    return mask.squeeze(0).squeeze(0).clamp(0, 1)


def _image_to_pil(image: torch.Tensor, mask: torch.Tensor | None) -> Image.Image:
    if image.ndim != 3:
        raise RuntimeError("Easy Save Image expects a single image, not an image batch.")

    image = image.detach().cpu().float().clamp(0, 1)
    height, width, channels = image.shape
    if channels < 3:
        raise RuntimeError("Easy Save Image expects image tensors with at least 3 channels.")

    rgb = (image[..., :3].numpy() * 255.0).clip(0, 255).astype(np.uint8)
    if mask is not None:
        alpha = (1.0 - _resize_mask(mask, width, height).numpy()).clip(0, 1)
        alpha = (alpha * 255.0).clip(0, 255).astype(np.uint8)
        rgba = np.dstack((rgb, alpha))
        return Image.fromarray(rgba, "RGBA")

    if channels >= 4:
        alpha = (image[..., 3].numpy() * 255.0).clip(0, 255).astype(np.uint8)
        rgba = np.dstack((rgb, alpha))
        return Image.fromarray(rgba, "RGBA")

    return Image.fromarray(rgb, "RGB")


def _save_pil_image(
    img: Image.Image,
    path: Path,
    prompt=None,
    extra_pnginfo=None,
    parameters: str = "",
    metadata_enabled: bool = True,
) -> None:
    ext = path.suffix.lower()
    if ext not in SAVE_EXTENSIONS:
        raise RuntimeError(f"Unsupported output extension: {path.suffix or '(none)'}")

    path.parent.mkdir(parents=True, exist_ok=True)
    if ext == ".png":
        metadata = None
        if metadata_enabled and not args.disable_metadata:
            metadata = PngInfo()
            if parameters:
                metadata.add_text("parameters", parameters)
            if prompt is not None:
                metadata.add_text("prompt", json.dumps(prompt))
            if extra_pnginfo is not None:
                for key, value in extra_pnginfo.items():
                    metadata.add_text(key, json.dumps(value))
        img.save(path, pnginfo=metadata, compress_level=4)
    elif ext == ".jpg":
        img.convert("RGB").save(path, format="JPEG", quality=100, subsampling=0)
    elif ext == ".webp":
        img.save(path, format="WEBP", lossless=True, quality=100, method=6, exact=True)
    else:
        raise RuntimeError(f"Unsupported output extension: {path.suffix or '(none)'}")


def _format_a1111_parameters(positive: str | None, negative: str | None) -> str:
    positive = str(positive or "").strip()
    negative = str(negative or "").strip()
    if positive and negative:
        return f"{positive}\nNegative prompt: {negative}"
    if negative:
        return f"Negative prompt: {negative}"
    return positive


def _requeue_next(job: dict) -> None:
    if not job.get("auto_requeue"):
        return

    import server

    next_index = int(job["index"]) + 1
    total = int(job["total"])
    start_index = int(job.get("start_index", 0))
    max_images = int(job.get("max_images", 0))
    if next_index >= total:
        return
    if max_images > 0 and next_index >= start_index + max_images:
        return

    queue = server.PromptServer.instance.prompt_queue
    running = queue.currently_running
    if not running:
        return

    run_id, value = next(iter(running.items()))
    node_id = str(job["node_id"])
    guard_key = (run_id, node_id, next_index)
    if guard_key in _requeued_runs:
        return
    _requeued_runs.add(guard_key)

    if len(value) == 6:
        number, _prompt_id, prompt, extra_data, outputs_to_execute, sensitive = value
    else:
        number, _prompt_id, prompt, extra_data, outputs_to_execute = value
        sensitive = {}

    prompt = copy.deepcopy(prompt)
    if node_id not in prompt:
        raise RuntimeError(f"Cannot requeue: folder loader node {node_id} is not in the prompt.")
    prompt[node_id]["inputs"]["current_index"] = next_index

    new_number = -server.PromptServer.instance.number
    server.PromptServer.instance.number += 1
    queue.put((new_number, str(uuid.uuid4()), prompt, extra_data, outputs_to_execute, sensitive))


class EasyImageNodesLoadImage:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("STRING", {"default": "", "multiline": False}),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("IMAGE", "MASK", "filename", "stem", "extension", "relative_path")
    FUNCTION = "load_image"
    CATEGORY = CATEGORY

    def load_image(self, image: str):
        relative_path = _clean_relative_path(image, "image")
        path = _as_input_path(relative_path)
        if not path.is_file():
            raise RuntimeError(f"Image does not exist under ComfyUI input: {relative_path}")
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            raise RuntimeError(f"Unsupported image extension: {path.suffix}")

        filename, stem, extension, clean_path = _path_metadata(relative_path)
        image_tensor, mask_tensor = _load_image_tensor(path)
        return (image_tensor, mask_tensor, filename, stem, extension, clean_path)

    @classmethod
    def IS_CHANGED(cls, image: str):
        try:
            return _hash_file(_as_input_path(image))
        except Exception:
            return "invalid"

    @classmethod
    def VALIDATE_INPUTS(cls, image: str):
        try:
            path = _as_input_path(image)
            if not path.is_file():
                return f"Image does not exist under ComfyUI input: {image}"
            if path.suffix.lower() not in IMAGE_EXTENSIONS:
                return f"Unsupported image extension: {path.suffix}"
        except Exception as exc:
            return str(exc)
        return True


class EasyImageNodesLoadImagesFromFolder:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "folder": ("STRING", {"default": "", "multiline": False}),
                "sort_order": (list(SORT_ORDERS), {"default": "ascending"}),
                "auto_requeue": ("BOOLEAN", {"default": False}),
                "start_index": ("INT", {"default": 0, "min": 0, "max": 1_000_000}),
                "max_images": ("INT", {"default": 0, "min": 0, "max": 1_000_000}),
                "current_index": ("INT", {"default": 0, "min": 0, "max": 1_000_000, "advanced": True}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "STRING", "STRING", "STRING", "INT", "INT", "EASY_IMAGE_JOB")
    RETURN_NAMES = ("IMAGE", "MASK", "filename", "stem", "extension", "relative_path", "index", "total", "job")
    FUNCTION = "load_image"
    CATEGORY = CATEGORY

    def load_image(
        self,
        folder: str,
        sort_order: str = "ascending",
        auto_requeue: bool = False,
        start_index: int = 0,
        max_images: int = 0,
        current_index: int = 0,
        unique_id=None,
    ):
        files = _list_input_images(folder, sort_order)
        effective_index = max(int(start_index), int(current_index))
        if effective_index >= len(files):
            raise RuntimeError(
                f"Image index {effective_index} is outside folder range 0..{len(files) - 1}."
            )
        if max_images > 0 and effective_index >= int(start_index) + int(max_images):
            raise RuntimeError(
                f"Image index {effective_index} is outside max_images limit from start_index {start_index}."
            )

        relative_path = files[effective_index]
        path = _as_input_path(f"{_clean_relative_path(folder, 'folder')}/{relative_path}")
        filename, stem, extension, clean_path = _path_metadata(relative_path)
        image_tensor, mask_tensor = _load_image_tensor(path)
        job = {
            "node_id": str(unique_id) if unique_id is not None else "",
            "folder": _clean_relative_path(folder, "folder"),
            "relative_path": clean_path,
            "sort_order": _normalize_sort_order(sort_order),
            "index": effective_index,
            "total": len(files),
            "start_index": int(start_index),
            "max_images": int(max_images),
            "auto_requeue": bool(auto_requeue),
        }
        return (
            image_tensor,
            mask_tensor,
            filename,
            stem,
            extension,
            clean_path,
            effective_index,
            len(files),
            job,
        )

    @classmethod
    def IS_CHANGED(
        cls,
        folder: str,
        sort_order: str = "ascending",
        auto_requeue: bool = False,
        start_index: int = 0,
        max_images: int = 0,
        current_index: int = 0,
    ):
        try:
            files = _list_input_images(folder, sort_order)
            effective_index = max(int(start_index), int(current_index))
            if effective_index >= len(files):
                return "invalid"
            path = _as_input_path(f"{_clean_relative_path(folder, 'folder')}/{files[effective_index]}")
            return f"{_normalize_sort_order(sort_order)}:{effective_index}:{_hash_file(path)}"
        except Exception:
            return "invalid"

    @classmethod
    def VALIDATE_INPUTS(
        cls,
        folder: str,
        sort_order: str = "ascending",
        start_index: int = 0,
        max_images: int = 0,
        current_index: int = 0,
        **kwargs,
    ):
        try:
            files = _list_input_images(folder, sort_order)
            effective_index = max(int(start_index), int(current_index))
            if effective_index >= len(files):
                return f"Image index {effective_index} is outside folder range 0..{len(files) - 1}."
            if max_images > 0 and effective_index >= int(start_index) + int(max_images):
                return f"Image index {effective_index} is outside max_images limit from start_index {start_index}."
        except Exception as exc:
            return str(exc)
        return True


class EasyImageNodesSaveImage:
    def __init__(self):
        self.output_dir = Path(folder_paths.get_output_directory()).resolve()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "filename": ("STRING", {"default": "", "multiline": False}),
                "extension_select": (["png", "jpg", "webp"], {"default": "png"}),
                "path_enabled": ("BOOLEAN", {"default": False}),
                "path": ("STRING", {"default": "", "multiline": False}),
            },
            "optional": {
                "exif_enabled": ("BOOLEAN", {"default": True}),
                "positive": ("STRING", {"default": "", "multiline": True}),
                "negative": ("STRING", {"default": "", "multiline": True}),
                "extension": ("STRING", {"forceInput": True}),
                "mask": ("MASK",),
                "job": ("EASY_IMAGE_JOB",),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_image"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    def save_image(
        self,
        images: torch.Tensor,
        filename: str,
        extension_select: str,
        path_enabled: bool,
        path: str,
        exif_enabled: bool = True,
        positive: str = "",
        negative: str = "",
        extension: str | None = None,
        mask: torch.Tensor | None = None,
        job: dict | None = None,
        prompt=None,
        extra_pnginfo=None,
        unique_id=None,
    ):
        if images.ndim != 4 or images.shape[0] != 1:
            raise RuntimeError("Easy Save Image expects exactly one image per execution.")
        if mask is not None and mask.ndim >= 3 and mask.shape[0] > 1:
            mask = mask[:1]

        save_extension = extension or extension_select
        if _is_linked_prompt_input(prompt, unique_id, "filename"):
            clean_filename = _replace_path_extension(filename, save_extension)
        else:
            clean_filename = _auto_increment_relative_path(
                filename,
                save_extension,
                self.output_dir,
                int(images.shape[2]),
                int(images.shape[1]),
                prompt=prompt,
            )

        output_parts = []
        if path_enabled:
            output_folder = _clean_optional_output_folder(path)
            if output_folder:
                output_parts.append(output_folder)
        output_parts.append(clean_filename)

        relative_output = "/".join(output_parts)
        output_path = (self.output_dir / relative_output).resolve()
        if os.path.commonpath((str(self.output_dir), str(output_path))) != str(self.output_dir):
            raise RuntimeError(f"Output path escapes the ComfyUI output directory: {relative_output}")

        pil_image = _image_to_pil(images[0], mask)
        parameters = _format_a1111_parameters(positive, negative)
        _save_pil_image(
            pil_image,
            output_path,
            prompt=prompt,
            extra_pnginfo=extra_pnginfo,
            parameters=parameters,
            metadata_enabled=exif_enabled,
        )

        subfolder = output_path.parent.relative_to(self.output_dir).as_posix()
        if subfolder == ".":
            subfolder = ""
        result = {
            "filename": output_path.name,
            "subfolder": subfolder,
            "type": "output",
        }

        if job:
            _requeue_next(job)

        return {"ui": {"images": [result]}}
