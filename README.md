# ComfyUI Easy Image Nodes

Languages: [English](#english) | [한국어](#한국어)

## English

### Features

- Load a single uploaded image along with its transparency, filename, and extension.
- Load images individually from an uploaded folder and all its subfolders, including each image's transparency, filename, and extension.
- Save images using the same filename and extension as the uploaded originals.
- Include EXIF metadata, such as positive and negative prompts, in saved images.
- Supports the output formats used by existing image save nodes.

### Installation

Open a terminal in your ComfyUI `custom_nodes` directory:

```bash
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/mengod-gh/ComfyUI-Easy-Image-Nodes.git
```

Restart ComfyUI after installation.
This has only been tested with ComfyUI Portable.

### Node: Easy Load Image

Loads a single image.
Uploaded images are automatically copied to the `input` folder in your ComfyUI Portable installation.

#### Inputs

| Name | Description |
| --- | --- |
| `image` | Use `choose image to upload` to upload and select an image. Uploaded images are automatically copied to the `input` folder. |

#### Outputs

| Name | Description |
| --- | --- |
| `IMAGE` | The uploaded image. |
| `MASK` | Transparency information from the image. |
| `filename` | Filename without the extension, for example `sample`. |
| `extension` | File extension including the dot, for example `.png`. |

### Node: Easy Load Images From Folder

Loads all images in a folder in order.
Use `choose folder to upload` to upload an entire folder to `input`, or enter an absolute path in `folder` to load it directly. Subfolders are detected automatically.

#### Inputs

| Name | Description |
| --- | --- |
| `folder` | Enter the image folder's absolute path (for example `/home/user/Pictures/`) or a path relative to ComfyUI `input`, or select a folder using `choose folder to upload`. |
| `sort_order` | Choose `ascending` or `descending` to load images in ascending or descending filename order. |
| `auto_requeue` | When enabled, automatically loads the next image once processing finishes. Connect `job` to Easy Save Image. |
| `start_index` | Sets which image to start processing from. Defaults to `0`. |
| `max_images` | Maximum number of images to process from `start_index`. `0` means no limit. |

#### Outputs

| Name | Description |
| --- | --- |
| `IMAGE` | The uploaded image. |
| `MASK` | Transparency information from the image. |
| `filename` | Filename without the extension, for example `sample`. |
| `extension` | Lowercase file extension including the dot, for example `.png`. |
| `relative_path` | Path relative to the uploaded folder. The selected top-level folder name is omitted, and subfolders are preserved when saving under `output`. |
| `job` | Internal job data used by Easy Save Image for `auto_requeue`. |

To process the whole folder, enable `auto_requeue`, connect `job` to Easy Save Image, and leave `start_index` and `max_images` at `0`. Queue once; each successful save queues the next image until the folder ends. Connecting `job` alone does not enable looping.

Connect `relative_path` to Easy Save Image's `filename` input to preserve the uploaded folder's structure under `output`. If you specify a `path` in Easy Save Image, the same structure is saved under `output/<specified path>/`.

### Node: Easy Save Image

Saves images to the ComfyUI `output` folder.

#### Inputs

| Name | Description |
| --- | --- |
| `images` | The image to save. |
| `filename` | When connected, saves using the original or specified filename, overwriting any existing file with the same name. If left blank and unconnected, appends a sequential number starting at `_0001` to the last component of `path`. |
| `extension_select` | Output format: `png`, `jpg`, or `webp`. |
| `path` | A configurable path under ComfyUI `output`, usually used to create folders. If `filename` is unconnected or blank, a sequential number is appended to the last component. End the path with `/` to keep it as a folder and use numbered filenames inside it. |
| `exif_enabled` | Defaults to `True`. Stores EXIF metadata in the saved image. |
| `positive` | When `exif_enabled` is on, stores the specified positive prompt in the image's EXIF metadata. |
| `negative` | When `exif_enabled` is on, stores the specified negative prompt in the image's EXIF metadata. |
| `extension` | Optional extension input. Connect the image loader's `extension` output to preserve the original format. Use PNG or WebP to preserve metadata for large workflows. |
| `mask` | Applies the original image's transparency when saving. |
| `job` | Connect the folder loader's `job` output here when using `auto_requeue`. To process all images in sequence, connect this input and enable `auto_requeue` in Easy Load Images From Folder. |

### License

MIT License. See [LICENSE](LICENSE) for details.

## 한국어

### 주요 기능

- 업로드한 단일 이미지의 투명 배경, 파일 이름, 확장자를 불러 올 수 있습니다. 
- 폴더 경로를 업로드 해서 그 폴더를 기준으로 모든 하위 폴더의 이미지들까지 각각 개별로 투명 배경, 파일 이름, 확장자를 불러올 수 있습니다. 
- 업로드한 이미지와 동일한 이름, 확장자를 자동으로 인식해서 이미지를 저장할 수 있습니다.
- 저장할 이미지의 EXIF 정보(긍정, 부정 프롬프트, 등)를 이미지 정보에 넣을 수 있습니다.
- 기존 이미지 저장 노드들이 지원하는 저장포맷을 그대로 사용 할 수 있습니다.

### 설치 방법

ComfyUI의 `custom_nodes` 폴더에서 터미널을 엽니다:

```bash
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/mengod-gh/ComfyUI-Easy-Image-Nodes.git
```

설치 후 ComfyUI를 재시작하세요.  
ComfyUI Portable에서만 정상 작동 여부 확인을 하였습니다.

### 노드: Easy Load Image

단일 이미지를 불러옵니다.  
업로드한 이미지는 ComfyUI Portable 폴더에 Input 폴더로 자동으로 복사되어 사용됩니다.

#### 입력

| 이름 | 의미 |
| --- | --- |
| `image` | `choose image to upload` 버튼으로 이미지를 업로드하고 선택할 수 있습니다. 업로드한 이미지는 `input` 폴더에 자동으로 복사됩니다. |

#### 출력

| 이름 | 의미 |
| --- | --- |
| `IMAGE` | 업로드한 이미지. |
| `MASK` | 투명 배경의 정보가 담겨있습니다. |
| `filename` | 확장자를 제외한 파일명입니다. 예: `sample` |
| `extension` | 점을 포함한 확장자명입니다. 예: `.png` |

### 노드: Easy Load Images From Folder

폴더에 있는 모든 이미지를 순서대로 불러옵니다.  
`choose folder to upload` 버튼으로 폴더를 통째로 input 폴더에 업로드 하거나, 노드에 있는 `folder`에 절대경로를 입력해서 폴더를 로드합니다. (하위폴더들은 자동으로 인식합니다.)

#### 입력

| 이름 | 의미 |
| --- | --- |
| `folder` | 업로드할 이미지들 폴더의 절대 경로(예: `/home/user/Pictures/`) 또는 ComfyUI input 폴더의 상대 경로를 입력하거나. `choose folder to upload` 버튼으로 경로를 선택합니다. |
| `sort_order` | `ascending` 또는 `descending`로 이미지를 이름 기준으로 오름차순으로 읽을 지 내림차순으로 읽을 지 정할 수 있습니다. |
| `auto_requeue` | 활성화하면 이미지 작업 완료 후 자동으로 다음 이미지를 로드합니다. `job`을 Easy Save Image에 연결해야 합니다. |
| `start_index` | 몇번째 이미지부터 처리하는 지 정합니다. 기본값은 `0`입니다. |
| `max_images` | `start_index`부터 처리할 최대 이미지 수입니다. `0`이면 제한이 없습니다. |

#### 출력

| 이름 | 의미 |
| --- | --- |
| `IMAGE` | 업로드한 이미지. |
| `MASK` | 투명 배경의 정보가 담겨있습니다. |
| `filename` | 확장자를 제외한 파일명입니다. 예: `sample` |
| `extension` | 점을 포함한 소문자 확장자입니다. 예: `.png` |
| `relative_path` | 업로드한 폴더의 상대 경로 정보가 들어가 있습니다. 선택한 최상위 폴더명은 제외되고 하위 폴더들은 output 폴더에 그대로 유지되어 저장됩니다. |
| `job` | `auto_requeue`를 위해 Easy Save Image가 사용하는 내부 작업 데이터입니다. |

전체 폴더를 처리하려면 `auto_requeue`를 켜고 `job`을 Easy Save Image에 연결한 뒤, `start_index`, `max_images`를 `0`으로 두세요. 한 번 실행하면 저장 성공 후 다음 이미지를 자동으로 큐에 넣고 마지막 이미지에서 멈춥니다. `job` 연결만으로는 반복이 활성화되지 않습니다.  
`relative_path`을 Easy Save Image 노드의 `filename`에 연결하면 output 폴더 기준, 업로드한 폴더랑 동일한 구조로 저장됩니다. 만약 Easy Save Image 노드의 `path`에 원하는 경로를 지정해주면 `output/<지정한 경로>/`에 똑같이 저장됩니다.

### 노드: Easy Save Image

이미지를 ComfyUI `output` 폴더에 저장합니다.

#### 입력

| 이름 | 의미 |
| --- | --- |
| `images` | 저장할 이미지입니다. |
| `filename` | 연결하면 원본 파일명 혹은 지정한 파일명으로 저장하며 똑같은 이름이 있을 시 기존 파일을 덮어씁니다. 만약 연결하지 않고 비어 있으면 `path`의 마지막 이름에 <_숫자> (0001부터 순서대로)를 붙여 이미지가 저장됩니다. |
| `extension_select` | 출력 포맷입니다: `png`, `jpg`, `webp` |
| `path` | ComfyUI `output` 폴더 아래의 설정 가능한 경로입니다. 일반적으로 폴더 생성 용도로 사용되지만 `filename`을 연결하지 않거나 비어 있으면 마지막 이름에 <_숫자>를 붙여 이미지가 저장되고 끝에 `/`를 붙이면 폴더로 유지하고 <_숫자>만 붙여서. 저장됩니다. |
| `exif_enabled` | 기본값은 `True`입니다. 저장한 이미지에 EXIF 정보가 저장됩니다. |
| `positive` | `exif_enabled`가 켜져 있을 때 EXIF 정보에 positive prompt (긍정 프롬프트)를 지정한 값으로 저장합니다. |
| `negative` | `exif_enabled`가 켜져 있을 때 EXIF 정보에 negative prompt (부정 프롬프트)를 지정한 값으로 저장합니다. |
| `extension` | 선택 확장자 입력입니다. 이미지 로더의 `extension`을 연결하면 원본 포맷을 유지할 수 있습니다. 용량이 큰 워크플로우의 메타데이터까지 보존하려면 PNG 또는 WebP를 사용하세요. |
| `mask` | 저장 시 원본 이미지의 투명 배경 부분을 적용합니다. |
| `job` | `auto_requeue`를 사용할 때 폴더 로더의 `job` 출력을 여기에 연결합니다. 이 부분을 연결하고 Easy Load Images From Folder의 `auto_requeue`을 활성화 해야 모든 이미지를 반복해서 로드합니다. |

### 라이선스

MIT 라이선스입니다. 자세한 내용은 [LICENSE](LICENSE)를 확인하세요.
