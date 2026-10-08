import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const IMAGE_EXTENSIONS = new Set([".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"]);

function chainCallback(object, property, callback) {
  if (!object) {
    return;
  }
  const original = object[property];
  object[property] = function (...args) {
    const result = original?.apply(this, args);
    callback.apply(this, args);
    return result;
  };
}

function getWidget(node, name) {
  return node.widgets?.find((widget) => widget.name === name);
}

function setWidgetValue(widget, value) {
  if (!widget) {
    return;
  }
  if (widget.options?.values && !widget.options.values.includes(value)) {
    widget.options.values.push(value);
  }
  widget.value = value;
  widget.callback?.(value);
}

function extensionOf(name) {
  const index = name.lastIndexOf(".");
  return index >= 0 ? name.slice(index).toLowerCase() : "";
}

function normalizeSubfolder(value) {
  return value.replaceAll("\\", "/").replace(/^\/+/, "");
}

function responsePath(data) {
  const subfolder = normalizeSubfolder(data.subfolder || "").replace(/\/+$/, "");
  return subfolder ? `${subfolder}/${data.name}` : data.name;
}

function splitRelativePath(value) {
  const relativePath = normalizeSubfolder(String(value || "").trim());
  if (!relativePath) {
    return null;
  }
  const slash = relativePath.lastIndexOf("/");
  if (slash < 0) {
    return { filename: relativePath, subfolder: "" };
  }
  return {
    filename: relativePath.slice(slash + 1),
    subfolder: relativePath.slice(0, slash),
  };
}

function refreshNodeSize(node) {
  requestAnimationFrame(() => {
    node.setSize([node.size[0], node.computeSize([node.size[0], node.size[1]])[1]]);
    node.graph?.setDirtyCanvas(true, true);
  });
}

function buildInputViewUrl(relativePath) {
  const parts = splitRelativePath(relativePath);
  if (!parts?.filename) {
    return "";
  }
  const params = new URLSearchParams({
    filename: parts.filename,
    type: "input",
    preview: "webp;90",
    timestamp: Date.now().toString(),
  });
  if (parts.subfolder) {
    params.set("subfolder", parts.subfolder);
  }
  return api.apiURL(`/view?${params}`);
}

async function uploadInputFile(file, subfolder = "", progressCallback = null) {
  const body = new FormData();
  body.append("image", new File([file], file.name, { type: file.type, lastModified: file.lastModified }));
  body.append("type", "input");
  body.append("overwrite", "true");
  if (subfolder) {
    body.append("subfolder", normalizeSubfolder(subfolder));
  }

  const response = await api.fetchApi("/upload/image", {
    method: "POST",
    body,
  });
  progressCallback?.();
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return await response.json();
}

function addButton(node, label, callback) {
  const button = node.addWidget("button", label, null, callback);
  button.options = button.options || {};
  button.options.serialize = false;
  return button;
}

function addImagePreview(node, imageWidget) {
  const container = document.createElement("div");
  container.style.width = "100%";
  container.style.overflow = "hidden";
  container.style.borderRadius = "4px";

  const img = document.createElement("img");
  img.style.display = "none";
  img.style.width = "100%";
  img.style.height = "auto";
  img.style.objectFit = "contain";
  img.draggable = false;
  container.appendChild(img);

  function previewHeight() {
    if (img.style.display === "none" || !img.naturalWidth || !img.naturalHeight) {
      return 0;
    }
    return Math.max(80, (node.size[0] - 20) * (img.naturalHeight / img.naturalWidth) + 10);
  }

  const previewWidget = node.addDOMWidget("easy_image_preview", "preview", container, {
    serialize: false,
    hideOnZoom: false,
    getMinHeight: previewHeight,
    getMaxHeight: previewHeight,
    getValue() {
      return imageWidget.value;
    },
    setValue(value) {
      updatePreview(value);
    },
  });

  previewWidget.computeSize = function (width) {
    return [width, previewHeight() || -4];
  };

  function updatePreview(value) {
    const url = buildInputViewUrl(value);
    if (!url) {
      img.removeAttribute("src");
      img.style.display = "none";
      refreshNodeSize(node);
      return;
    }
    img.style.display = "block";
    img.src = url;
  }

  img.onload = () => refreshNodeSize(node);
  img.onerror = () => {
    img.removeAttribute("src");
    img.style.display = "none";
    refreshNodeSize(node);
  };

  chainCallback(imageWidget, "callback", function (value) {
    updatePreview(value);
  });
  updatePreview(imageWidget.value);
}

function addSingleImageUpload(node) {
  const imageWidget = getWidget(node, "image");
  if (!imageWidget) {
    return;
  }

  addImagePreview(node, imageWidget);

  const fileInput = document.createElement("input");
  fileInput.type = "file";
  fileInput.accept = [...IMAGE_EXTENSIONS].join(",");
  fileInput.style.display = "none";
  document.body.appendChild(fileInput);

  chainCallback(node, "onRemoved", () => fileInput.remove());
  addButton(node, "choose image to upload", () => {
    fileInput.value = "";
    fileInput.click();
  });

  fileInput.onchange = async () => {
    const file = fileInput.files?.[0];
    if (!file) {
      return;
    }
    if (!IMAGE_EXTENSIONS.has(extensionOf(file.name))) {
      alert(`Unsupported image file: ${file.name}`);
      return;
    }
    try {
      node.progress = 0.25;
      const data = await uploadInputFile(file, "", () => {
        node.progress = 1;
      });
      setWidgetValue(imageWidget, responsePath(data));
    } catch (error) {
      alert(`Image upload failed: ${error}`);
    } finally {
      node.progress = undefined;
    }
  };
}

function addFolderUpload(node) {
  const folderWidget = getWidget(node, "folder");
  if (!folderWidget) {
    return;
  }

  const fileInput = document.createElement("input");
  fileInput.type = "file";
  const supportsFolderUpload = "webkitdirectory" in fileInput;
  fileInput.webkitdirectory = true;
  fileInput.multiple = true;
  fileInput.style.display = "none";
  document.body.appendChild(fileInput);

  chainCallback(node, "onRemoved", () => fileInput.remove());
  addButton(node, "choose folder to upload", () => {
    if (!supportsFolderUpload) {
      alert("This browser does not support folder uploads. Enter a folder path on the ComfyUI server, or use a browser with folder upload support.");
      return;
    }
    fileInput.value = "";
    fileInput.click();
  });

  fileInput.onchange = async () => {
    const files = [...(fileInput.files || [])].filter((file) => IMAGE_EXTENSIONS.has(extensionOf(file.name)));
    if (files.length === 0) {
      alert("No supported image files found in the selected folder.");
      return;
    }

    const firstPath = files[0].webkitRelativePath || files[0].name;
    const topFolder = firstPath.includes("/") ? firstPath.split("/")[0] : "";
    if (!topFolder) {
      alert("The selected folder path could not be read by the browser.");
      return;
    }

    try {
      let uploaded = 0;
      for (const file of files) {
        const relativePath = file.webkitRelativePath || file.name;
        const slash = relativePath.lastIndexOf("/");
        const subfolder = slash >= 0 ? relativePath.slice(0, slash + 1) : topFolder + "/";
        await uploadInputFile(file, subfolder, () => {
          uploaded += 1;
          node.progress = uploaded / files.length;
        });
      }
      setWidgetValue(folderWidget, topFolder);
    } catch (error) {
      alert(`Folder upload failed: ${error}`);
    } finally {
      node.progress = undefined;
    }
  };
}

function isEasySaveImageNode(node) {
  return (node?.comfyClass || node?.type) === "EasyImageNodes_SaveImage";
}

function migrateFolderOutputs(node) {
  if ((node?.comfyClass || node?.type) !== "EasyImageNodes_LoadImagesFromFolder") {
    return;
  }
  const stemIndex = node.outputs?.findIndex((output) => output.name === "stem") ?? -1;
  if (stemIndex >= 0) {
    const filenameIndex = node.outputs.findIndex((output) => output.name === "filename");
    const stem = node.outputs[stemIndex];
    for (const linkId of [...(stem.links || [])]) {
      const link = node.graph.links[linkId];
      if (link) {
        node.connect(filenameIndex, node.graph.getNodeById(link.target_id), link.target_slot);
      }
    }
    node.removeOutput(stemIndex);
  }
  for (let index = (node.outputs?.length || 0) - 1; index >= 0; index -= 1) {
    if (["index", "total"].includes(node.outputs[index].name)) {
      node.removeOutput(index);
    }
  }
}

function migrateSaveImageSlots(node) {
  if (!isEasySaveImageNode(node)) {
    return;
  }
  const pathEnabledIndex = node.inputs?.findIndex((input) => input.name === "path_enabled") ?? -1;
  if (pathEnabledIndex >= 0) {
    node.removeInput(pathEnabledIndex);
  }
  for (let index = (node.outputs?.length || 0) - 1; index >= 0; index -= 1) {
    if (typeof node.removeOutput === "function") {
      node.removeOutput(index);
    } else {
      node.outputs.splice(index, 1);
    }
  }
  node.graph?.setDirtyCanvas(true, true);
}

app.registerExtension({
  name: "ComfyUI.EasyImageNodes.Uploads",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData?.name === "EasyImageNodes_LoadImage") {
      chainCallback(nodeType.prototype, "onNodeCreated", function () {
        addSingleImageUpload(this);
      });
    }

    if (nodeData?.name === "EasyImageNodes_LoadImagesFromFolder") {
      chainCallback(nodeType.prototype, "onNodeCreated", function () {
        const currentIndexWidget = getWidget(this, "current_index");
        if (currentIndexWidget) {
          currentIndexWidget.hidden = true;
          currentIndexWidget.type = "converted-widget";
          currentIndexWidget.computeSize = () => [0, -4];
        }
        addFolderUpload(this);
      });
    }

    if (nodeData?.name === "EasyImageNodes_SaveImage") {
      chainCallback(nodeType.prototype, "onNodeCreated", function () {
        migrateSaveImageSlots(this);
      });
      const configure = nodeType.prototype.configure;
      nodeType.prototype.configure = function (info, ...args) {
        if (Array.isArray(info.widgets_values) && typeof info.widgets_values[2] === "boolean") {
          const widgetsValues = [...info.widgets_values];
          widgetsValues.splice(2, 1);
          info = { ...info, widgets_values: widgetsValues };
        }
        const result = configure?.call(this, info, ...args);
        migrateSaveImageSlots(this);
        return result;
      };
    }
  },
  loadedGraphNode(node) {
    migrateFolderOutputs(node);
    migrateSaveImageSlots(node);
  },
});
