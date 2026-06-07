# ComfyUI Easy Image Nodes

Dataset-oriented image load and save nodes for ComfyUI.

These nodes are built for workflows where you load an image, process it, and save the result with the same filename or with a controlled auto-incrementing filename.

Languages: [English](#english) | [한국어](#한국어) | [日本語](#日本語) | [中文](#中文)

## English

### Features

- Load one image from ComfyUI `input` and output its filename metadata.
- Load images from an uploaded folder one at a time, sorted ascending or descending.
- Preserve alpha information through the `MASK` output.
- Save processed images with the loaded filename.
- Save to optional subfolders under ComfyUI `output`.
- Save as `png`, `jpg`, or `webp`.
- Auto-increment filenames when the save `filename` widget is not connected.
- Supports `%date:yyyy-MM-dd%`, `%width%`, `%height%`, and `%Node Title.input_name%` tokens in unconnected save filename prefixes.

### Installation

Open a terminal in your ComfyUI `custom_nodes` directory:

```bash
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/YOUR_USERNAME/ComfyUI-EasyImageNodes.git
```

Restart ComfyUI after installation.

### Security Model

- The image upload button uploads files into ComfyUI `input`.
- The folder upload button uploads the selected folder into ComfyUI `input`.
- Load nodes only read paths inside ComfyUI `input`.
- Save nodes only write paths inside ComfyUI `output`.
- Absolute paths and `..` path traversal are rejected.
- The selected top-level folder name is not repeated in the folder loader `relative_path` output.

### Node: Easy Load Image

Loads a single image from ComfyUI `input`.

#### Inputs

| Name | Type | Meaning |
| --- | --- | --- |
| `image` | STRING | Image path relative to ComfyUI `input`. Use the `choose image to upload` button to upload and select an image. |

#### Outputs

| Name | Type | Meaning |
| --- | --- | --- |
| `IMAGE` | IMAGE | Loaded RGB image tensor. |
| `MASK` | MASK | Alpha-derived mask. Opaque pixels are `0`, transparent pixels are `1`. |
| `filename` | STRING | Full filename with extension, for example `sample.png`. |
| `stem` | STRING | Filename without extension, for example `sample`. |
| `extension` | STRING | Lowercase extension with dot, for example `.png`. |
| `relative_path` | STRING | Path relative to ComfyUI `input`, preserving subfolders. |

### Node: Easy Load Images From Folder

Loads one image per execution from a folder under ComfyUI `input`.

Use `choose folder to upload` to upload a local folder into ComfyUI `input`. The node scans supported images recursively.

#### Inputs

| Name | Type | Meaning |
| --- | --- | --- |
| `folder` | STRING | Folder path relative to ComfyUI `input`. |
| `sort_order` | COMBO | `ascending` or `descending`, sorted by recursive relative path and filename. |
| `auto_requeue` | BOOLEAN | If `True`, the save node can queue the next image automatically after a successful save. Connect `job` to Easy Save Image. |
| `start_index` | INT | First image index to process. Default `0`. |
| `max_images` | INT | Maximum number of images to process from `start_index`. `0` means no limit. |
| `current_index` | INT | Advanced internal/resume index. Normally leave this at `0`. During auto requeue, the queued prompt copy is updated internally; the visible widget may not change. |

#### Outputs

| Name | Type | Meaning |
| --- | --- | --- |
| `IMAGE` | IMAGE | Loaded RGB image tensor. |
| `MASK` | MASK | Alpha-derived mask. Opaque pixels are `0`, transparent pixels are `1`. |
| `filename` | STRING | Full filename with extension. |
| `stem` | STRING | Filename without extension. |
| `extension` | STRING | Lowercase extension with dot. |
| `relative_path` | STRING | Path relative to the selected folder, excluding the selected top-level folder name. |
| `index` | INT | Current image index in the sorted file list. |
| `total` | INT | Total number of supported images in the folder. |
| `job` | EASY_IMAGE_JOB | Internal job data used by Easy Save Image for `auto_requeue`. |

### Node: Easy Save Image

Saves exactly one image per execution into ComfyUI `output`.

#### Inputs

| Name | Type | Meaning |
| --- | --- | --- |
| `images` | IMAGE | Image to save. This node expects exactly one image per execution. |
| `filename` | STRING | If connected, this is treated as the exact output filename and existing files are overwritten. If unconnected, this is treated as an auto-incrementing filename prefix. |
| `extension_select` | COMBO | Output format: `png`, `jpg`, or `webp`. |
| `path_enabled` | BOOLEAN | If `True`, use `path` as an output subfolder under ComfyUI `output`. |
| `path` | STRING | Relative output subfolder, for example `datasets/sample`. Ignored when `path_enabled` is `False`. |
| `extension` | STRING, optional | Optional extension input. Connect loader `extension` here to preserve the original format. Overrides `extension_select`. |
| `mask` | MASK, optional | Optional mask used as alpha when saving. Mask `0` is opaque and mask `1` is transparent. |
| `job` | EASY_IMAGE_JOB, optional | Connect the folder loader `job` output here when using `auto_requeue`. |

#### Outputs

Easy Save Image has no output ports. It returns saved image UI data for ComfyUI preview/history.

#### Filename Behavior

When `filename` is connected:

```text
sample.png -> output/sample.png
sub/sample.png + path=cleaned -> output/cleaned/sub/sample.png
```

Existing files with the same path are overwritten.

When `filename` is not connected:

```text
blank filename -> output/0001.png, output/0002.png
anima -> output/anima_0001.png, output/anima_0002.png
%date:yyyy-MM-dd%/anima -> output/2026-06-07/anima_0001.png
```

Existing files are not overwritten in this auto-increment mode.

### Folder Workflow Example

If you upload a folder that contains:

```text
DatasetRoot/dataset/sample1.png
DatasetRoot/dataset/sample2.png
```

`Easy Load Images From Folder` with `folder=DatasetRoot` outputs:

```text
dataset/sample1.png
dataset/sample2.png
```

Connect `relative_path` to Easy Save Image `filename` to save:

```text
output/dataset/sample1.png
output/dataset/sample2.png
```

With `path_enabled=True` and `path=cleaned`, the files save to:

```text
output/cleaned/dataset/sample1.png
output/cleaned/dataset/sample2.png
```

## 한국어

### 주요 기능

- ComfyUI `input`에서 단일 이미지를 불러오고 파일명 정보를 출력합니다.
- 업로드한 폴더에서 이미지를 하나씩 불러오며 오름차순/내림차순 정렬을 선택할 수 있습니다.
- PNG 같은 투명 이미지의 알파 정보를 `MASK`로 출력합니다.
- 처리된 이미지를 불러온 파일명 그대로 저장할 수 있습니다.
- ComfyUI `output` 아래의 선택한 하위 폴더에 저장할 수 있습니다.
- `png`, `jpg`, `webp` 저장을 지원합니다.
- 저장 노드의 `filename`이 연결되지 않은 경우 자동 증가 파일명을 사용합니다.
- 연결되지 않은 저장 filename prefix에서 `%date:yyyy-MM-dd%`, `%width%`, `%height%`, `%Node Title.input_name%` 토큰을 지원합니다.

### 설치 방법

ComfyUI의 `custom_nodes` 폴더에서 터미널을 엽니다:

```bash
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/YOUR_USERNAME/ComfyUI-EasyImageNodes.git
```

설치 후 ComfyUI를 재시작하세요.

### 보안 모델

- 이미지 선택 버튼은 파일을 ComfyUI `input`으로 업로드합니다.
- 폴더 선택 버튼은 선택한 폴더를 ComfyUI `input`으로 업로드합니다.
- 로드 노드는 ComfyUI `input` 내부 경로만 읽습니다.
- 저장 노드는 ComfyUI `output` 내부 경로에만 씁니다.
- 절대 경로와 `..` 경로 탈출은 차단됩니다.
- 폴더 로더의 `relative_path` 출력에는 선택한 최상위 폴더명이 반복되지 않습니다.

### 노드: Easy Load Image

ComfyUI `input` 안의 단일 이미지를 불러옵니다.

#### 입력

| 이름 | 타입 | 의미 |
| --- | --- | --- |
| `image` | STRING | ComfyUI `input` 기준 이미지 경로입니다. `choose image to upload` 버튼으로 업로드하고 선택할 수 있습니다. |

#### 출력

| 이름 | 타입 | 의미 |
| --- | --- | --- |
| `IMAGE` | IMAGE | 불러온 RGB 이미지 텐서입니다. |
| `MASK` | MASK | 알파에서 만든 마스크입니다. 불투명 픽셀은 `0`, 투명 픽셀은 `1`입니다. |
| `filename` | STRING | 확장자를 포함한 파일명입니다. 예: `sample.png`. |
| `stem` | STRING | 확장자를 제외한 파일명입니다. 예: `sample`. |
| `extension` | STRING | 점을 포함한 소문자 확장자입니다. 예: `.png`. |
| `relative_path` | STRING | ComfyUI `input` 기준 상대 경로이며 하위 폴더 구조를 보존합니다. |

### 노드: Easy Load Images From Folder

ComfyUI `input` 아래 폴더에서 실행마다 이미지 한 장을 불러옵니다.

`choose folder to upload` 버튼으로 로컬 폴더를 ComfyUI `input`에 업로드할 수 있습니다. 지원되는 이미지는 하위 폴더까지 재귀적으로 검색됩니다.

#### 입력

| 이름 | 타입 | 의미 |
| --- | --- | --- |
| `folder` | STRING | ComfyUI `input` 기준 폴더 경로입니다. |
| `sort_order` | COMBO | `ascending` 또는 `descending`입니다. 재귀 상대 경로와 파일명 기준으로 정렬합니다. |
| `auto_requeue` | BOOLEAN | `True`이면 저장 성공 후 다음 이미지를 자동으로 큐에 넣을 수 있습니다. `job`을 Easy Save Image에 연결해야 합니다. |
| `start_index` | INT | 처리 시작 이미지 인덱스입니다. 기본값은 `0`입니다. |
| `max_images` | INT | `start_index`부터 처리할 최대 이미지 수입니다. `0`이면 제한이 없습니다. |
| `current_index` | INT | 고급 내부/재개용 인덱스입니다. 보통 `0`으로 둡니다. 자동 재실행 시에는 서버 큐에 들어가는 prompt 복사본만 내부적으로 바뀌므로 화면의 위젯 값은 바뀌지 않을 수 있습니다. |

#### 출력

| 이름 | 타입 | 의미 |
| --- | --- | --- |
| `IMAGE` | IMAGE | 불러온 RGB 이미지 텐서입니다. |
| `MASK` | MASK | 알파에서 만든 마스크입니다. 불투명 픽셀은 `0`, 투명 픽셀은 `1`입니다. |
| `filename` | STRING | 확장자를 포함한 파일명입니다. |
| `stem` | STRING | 확장자를 제외한 파일명입니다. |
| `extension` | STRING | 점을 포함한 소문자 확장자입니다. |
| `relative_path` | STRING | 선택한 폴더 기준 상대 경로입니다. 선택한 최상위 폴더명은 제외됩니다. |
| `index` | INT | 정렬된 파일 목록에서 현재 이미지의 인덱스입니다. |
| `total` | INT | 폴더 안의 지원 이미지 전체 개수입니다. |
| `job` | EASY_IMAGE_JOB | `auto_requeue`를 위해 Easy Save Image가 사용하는 내부 작업 데이터입니다. |

### 노드: Easy Save Image

실행마다 이미지 한 장을 ComfyUI `output`에 저장합니다.

#### 입력

| 이름 | 타입 | 의미 |
| --- | --- | --- |
| `images` | IMAGE | 저장할 이미지입니다. 이 노드는 실행마다 정확히 한 장의 이미지를 기대합니다. |
| `filename` | STRING | 연결된 경우 정확한 출력 파일명으로 처리하며 기존 파일을 덮어씁니다. 연결되지 않은 경우 자동 증가 파일명 prefix로 처리합니다. |
| `extension_select` | COMBO | 출력 포맷입니다: `png`, `jpg`, `webp`. |
| `path_enabled` | BOOLEAN | `True`이면 `path`를 ComfyUI `output` 아래 하위 폴더로 사용합니다. |
| `path` | STRING | 상대 출력 하위 폴더입니다. 예: `datasets/sample`. `path_enabled`가 `False`이면 무시됩니다. |
| `extension` | STRING, optional | 선택 확장자 입력입니다. 로더의 `extension`을 연결하면 원본 포맷을 유지할 수 있습니다. `extension_select`보다 우선합니다. |
| `mask` | MASK, optional | 저장 시 알파로 사용할 선택 마스크입니다. 마스크 `0`은 불투명, `1`은 투명입니다. |
| `job` | EASY_IMAGE_JOB, optional | `auto_requeue`를 사용할 때 폴더 로더의 `job` 출력을 여기에 연결합니다. |

#### 출력

Easy Save Image에는 출력 포트가 없습니다. ComfyUI 미리보기/히스토리용 저장 이미지 UI 데이터만 반환합니다.

#### 파일명 동작

`filename`이 연결된 경우:

```text
sample.png -> output/sample.png
sub/sample.png + path=cleaned -> output/cleaned/sub/sample.png
```

같은 경로의 기존 파일은 덮어씁니다.

`filename`이 연결되지 않은 경우:

```text
빈 filename -> output/0001.png, output/0002.png
anima -> output/anima_0001.png, output/anima_0002.png
%date:yyyy-MM-dd%/anima -> output/2026-06-07/anima_0001.png
```

자동 증가 모드에서는 기존 파일을 덮어쓰지 않습니다.

### 폴더 워크플로우 예시

다음 폴더를 업로드했다고 가정합니다:

```text
DatasetRoot/dataset/sample1.png
DatasetRoot/dataset/sample2.png
```

`Easy Load Images From Folder`에서 `folder=DatasetRoot`이면 `relative_path`는 다음처럼 출력됩니다:

```text
dataset/sample1.png
dataset/sample2.png
```

`relative_path`를 Easy Save Image의 `filename`에 연결하면 다음처럼 저장됩니다:

```text
output/dataset/sample1.png
output/dataset/sample2.png
```

`path_enabled=True`, `path=cleaned`이면 다음처럼 저장됩니다:

```text
output/cleaned/dataset/sample1.png
output/cleaned/dataset/sample2.png
```

## 日本語

### 主な機能

- ComfyUI の `input` から単一画像を読み込み、ファイル名メタデータを出力します。
- アップロードしたフォルダー内の画像を 1 回の実行につき 1 枚ずつ読み込み、昇順または降順を選べます。
- 透過画像のアルファ情報を `MASK` として出力します。
- 処理後の画像を読み込んだファイル名のまま保存できます。
- ComfyUI の `output` 配下の任意のサブフォルダーに保存できます。
- `png`, `jpg`, `webp` で保存できます。
- 保存ノードの `filename` が接続されていない場合は、自動連番のファイル名を使います。
- 未接続の保存 filename prefix では `%date:yyyy-MM-dd%`, `%width%`, `%height%`, `%Node Title.input_name%` トークンを使えます。

### インストール

ComfyUI の `custom_nodes` ディレクトリでターミナルを開きます:

```bash
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/YOUR_USERNAME/ComfyUI-EasyImageNodes.git
```

インストール後、ComfyUI を再起動してください。

### セキュリティモデル

- 画像選択ボタンはファイルを ComfyUI `input` にアップロードします。
- フォルダー選択ボタンは選択したフォルダーを ComfyUI `input` にアップロードします。
- ロードノードは ComfyUI `input` 内のパスだけを読み込みます。
- 保存ノードは ComfyUI `output` 内のパスだけに書き込みます。
- 絶対パスと `..` によるパストラバーサルは拒否されます。
- フォルダーローダーの `relative_path` 出力には、選択した最上位フォルダー名は含まれません。

### ノード: Easy Load Image

ComfyUI `input` 内の単一画像を読み込みます。

#### 入力

| 名前 | 型 | 説明 |
| --- | --- | --- |
| `image` | STRING | ComfyUI `input` からの相対画像パスです。`choose image to upload` ボタンでアップロードして選択できます。 |

#### 出力

| 名前 | 型 | 説明 |
| --- | --- | --- |
| `IMAGE` | IMAGE | 読み込まれた RGB 画像テンソルです。 |
| `MASK` | MASK | アルファから作成されたマスクです。不透明ピクセルは `0`、透明ピクセルは `1` です。 |
| `filename` | STRING | 拡張子付きのファイル名です。例: `sample.png`。 |
| `stem` | STRING | 拡張子なしのファイル名です。例: `sample`。 |
| `extension` | STRING | ドット付きの小文字拡張子です。例: `.png`。 |
| `relative_path` | STRING | ComfyUI `input` からの相対パスで、サブフォルダー構造を保持します。 |

### ノード: Easy Load Images From Folder

ComfyUI `input` 配下のフォルダーから、実行ごとに 1 枚の画像を読み込みます。

`choose folder to upload` ボタンでローカルフォルダーを ComfyUI `input` にアップロードできます。対応画像はサブフォルダーまで再帰的に検索されます。

#### 入力

| 名前 | 型 | 説明 |
| --- | --- | --- |
| `folder` | STRING | ComfyUI `input` からの相対フォルダーパスです。 |
| `sort_order` | COMBO | `ascending` または `descending` です。再帰的な相対パスとファイル名で並べます。 |
| `auto_requeue` | BOOLEAN | `True` の場合、保存成功後に次の画像を自動でキューに入れられます。`job` を Easy Save Image に接続してください。 |
| `start_index` | INT | 処理を開始する画像インデックスです。デフォルトは `0` です。 |
| `max_images` | INT | `start_index` から処理する最大枚数です。`0` は制限なしです。 |
| `current_index` | INT | 高度な内部/再開用インデックスです。通常は `0` のままにします。自動再実行では、キューに入る prompt コピーだけが内部的に更新されるため、画面上のウィジェット値は変わらない場合があります。 |

#### 出力

| 名前 | 型 | 説明 |
| --- | --- | --- |
| `IMAGE` | IMAGE | 読み込まれた RGB 画像テンソルです。 |
| `MASK` | MASK | アルファから作成されたマスクです。不透明ピクセルは `0`、透明ピクセルは `1` です。 |
| `filename` | STRING | 拡張子付きのファイル名です。 |
| `stem` | STRING | 拡張子なしのファイル名です。 |
| `extension` | STRING | ドット付きの小文字拡張子です。 |
| `relative_path` | STRING | 選択フォルダーからの相対パスです。選択した最上位フォルダー名は除外されます。 |
| `index` | INT | ソート済みファイルリスト内の現在画像インデックスです。 |
| `total` | INT | フォルダー内の対応画像の総数です。 |
| `job` | EASY_IMAGE_JOB | `auto_requeue` のために Easy Save Image が使う内部ジョブデータです。 |

### ノード: Easy Save Image

実行ごとに 1 枚の画像を ComfyUI `output` に保存します。

#### 入力

| 名前 | 型 | 説明 |
| --- | --- | --- |
| `images` | IMAGE | 保存する画像です。このノードは 1 回の実行につき正確に 1 枚の画像を想定しています。 |
| `filename` | STRING | 接続されている場合は正確な出力ファイル名として扱い、既存ファイルを上書きします。未接続の場合は自動連番の filename prefix として扱います。 |
| `extension_select` | COMBO | 出力形式です: `png`, `jpg`, `webp`。 |
| `path_enabled` | BOOLEAN | `True` の場合、`path` を ComfyUI `output` 配下のサブフォルダーとして使います。 |
| `path` | STRING | 相対出力サブフォルダーです。例: `datasets/sample`。`path_enabled` が `False` の場合は無視されます。 |
| `extension` | STRING, optional | 任意の拡張子入力です。ローダーの `extension` を接続すると元形式を保持できます。`extension_select` より優先されます。 |
| `mask` | MASK, optional | 保存時のアルファとして使う任意マスクです。マスク `0` は不透明、`1` は透明です。 |
| `job` | EASY_IMAGE_JOB, optional | `auto_requeue` を使う場合、フォルダーローダーの `job` 出力をここに接続します。 |

#### 出力

Easy Save Image には出力ポートはありません。ComfyUI のプレビュー/履歴用の保存画像 UI データを返します。

#### ファイル名の動作

`filename` が接続されている場合:

```text
sample.png -> output/sample.png
sub/sample.png + path=cleaned -> output/cleaned/sub/sample.png
```

同じパスの既存ファイルは上書きされます。

`filename` が接続されていない場合:

```text
空の filename -> output/0001.png, output/0002.png
anima -> output/anima_0001.png, output/anima_0002.png
%date:yyyy-MM-dd%/anima -> output/2026-06-07/anima_0001.png
```

自動連番モードでは既存ファイルを上書きしません。

### フォルダーワークフロー例

次のフォルダーをアップロードしたとします:

```text
DatasetRoot/dataset/sample1.png
DatasetRoot/dataset/sample2.png
```

`Easy Load Images From Folder` で `folder=DatasetRoot` の場合、`relative_path` は次のように出力されます:

```text
dataset/sample1.png
dataset/sample2.png
```

`relative_path` を Easy Save Image の `filename` に接続すると、次のように保存されます:

```text
output/dataset/sample1.png
output/dataset/sample2.png
```

`path_enabled=True`, `path=cleaned` の場合は次のように保存されます:

```text
output/cleaned/dataset/sample1.png
output/cleaned/dataset/sample2.png
```

## 中文

### 主要功能

- 从 ComfyUI `input` 加载单张图片，并输出文件名信息。
- 从上传的文件夹中每次执行加载一张图片，可选择升序或降序。
- 通过 `MASK` 输出保留透明图片的 alpha 信息。
- 将处理后的图片按加载时的文件名保存。
- 可保存到 ComfyUI `output` 下的指定子文件夹。
- 支持保存为 `png`, `jpg`, `webp`。
- 当保存节点的 `filename` 未连接时，使用自动递增文件名。
- 未连接的保存 filename prefix 支持 `%date:yyyy-MM-dd%`, `%width%`, `%height%`, `%Node Title.input_name%` token。

### 安装方法

在 ComfyUI 的 `custom_nodes` 目录中打开终端:

```bash
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/YOUR_USERNAME/ComfyUI-EasyImageNodes.git
```

安装后重启 ComfyUI。

### 安全模型

- 图片选择按钮会把文件上传到 ComfyUI `input`。
- 文件夹选择按钮会把选中的文件夹上传到 ComfyUI `input`。
- 加载节点只读取 ComfyUI `input` 内部路径。
- 保存节点只写入 ComfyUI `output` 内部路径。
- 绝对路径和 `..` 路径穿越会被拒绝。
- 文件夹加载节点的 `relative_path` 输出不会重复包含所选的顶层文件夹名。

### 节点: Easy Load Image

从 ComfyUI `input` 中加载单张图片。

#### 输入

| 名称 | 类型 | 含义 |
| --- | --- | --- |
| `image` | STRING | 相对于 ComfyUI `input` 的图片路径。可用 `choose image to upload` 按钮上传并选择图片。 |

#### 输出

| 名称 | 类型 | 含义 |
| --- | --- | --- |
| `IMAGE` | IMAGE | 加载后的 RGB 图片张量。 |
| `MASK` | MASK | 从 alpha 生成的遮罩。不透明像素为 `0`，透明像素为 `1`。 |
| `filename` | STRING | 带扩展名的完整文件名，例如 `sample.png`。 |
| `stem` | STRING | 不带扩展名的文件名，例如 `sample`。 |
| `extension` | STRING | 带点的小写扩展名，例如 `.png`。 |
| `relative_path` | STRING | 相对于 ComfyUI `input` 的路径，并保留子文件夹结构。 |

### 节点: Easy Load Images From Folder

从 ComfyUI `input` 下的文件夹中，每次执行加载一张图片。

使用 `choose folder to upload` 可以把本地文件夹上传到 ComfyUI `input`。节点会递归扫描支持的图片。

#### 输入

| 名称 | 类型 | 含义 |
| --- | --- | --- |
| `folder` | STRING | 相对于 ComfyUI `input` 的文件夹路径。 |
| `sort_order` | COMBO | `ascending` 或 `descending`，按递归相对路径和文件名排序。 |
| `auto_requeue` | BOOLEAN | 如果为 `True`，保存成功后可以自动把下一张图片加入队列。需要把 `job` 连接到 Easy Save Image。 |
| `start_index` | INT | 开始处理的图片索引。默认值为 `0`。 |
| `max_images` | INT | 从 `start_index` 开始最多处理的图片数量。`0` 表示不限制。 |
| `current_index` | INT | 高级内部/恢复用索引。通常保持 `0`。自动重新排队时，只会在服务器队列中的 prompt 副本里更新，界面上的 widget 值可能不会变化。 |

#### 输出

| 名称 | 类型 | 含义 |
| --- | --- | --- |
| `IMAGE` | IMAGE | 加载后的 RGB 图片张量。 |
| `MASK` | MASK | 从 alpha 生成的遮罩。不透明像素为 `0`，透明像素为 `1`。 |
| `filename` | STRING | 带扩展名的完整文件名。 |
| `stem` | STRING | 不带扩展名的文件名。 |
| `extension` | STRING | 带点的小写扩展名。 |
| `relative_path` | STRING | 相对于所选文件夹的路径，不包含所选顶层文件夹名。 |
| `index` | INT | 当前图片在排序后文件列表中的索引。 |
| `total` | INT | 文件夹内支持图片的总数。 |
| `job` | EASY_IMAGE_JOB | Easy Save Image 用于 `auto_requeue` 的内部任务数据。 |

### 节点: Easy Save Image

每次执行把一张图片保存到 ComfyUI `output`。

#### 输入

| 名称 | 类型 | 含义 |
| --- | --- | --- |
| `images` | IMAGE | 要保存的图片。此节点每次执行只接受一张图片。 |
| `filename` | STRING | 如果已连接，则作为精确输出文件名处理，并覆盖已有文件。如果未连接，则作为自动递增的文件名前缀处理。 |
| `extension_select` | COMBO | 输出格式: `png`, `jpg`, `webp`。 |
| `path_enabled` | BOOLEAN | 如果为 `True`，使用 `path` 作为 ComfyUI `output` 下的子文件夹。 |
| `path` | STRING | 相对输出子文件夹，例如 `datasets/sample`。当 `path_enabled` 为 `False` 时会被忽略。 |
| `extension` | STRING, optional | 可选扩展名输入。连接加载节点的 `extension` 可保留原始格式。优先于 `extension_select`。 |
| `mask` | MASK, optional | 保存时作为 alpha 使用的可选遮罩。遮罩 `0` 为不透明，`1` 为透明。 |
| `job` | EASY_IMAGE_JOB, optional | 使用 `auto_requeue` 时，把文件夹加载节点的 `job` 输出连接到这里。 |

#### 输出

Easy Save Image 没有输出端口。它会返回用于 ComfyUI 预览/历史记录的保存图片 UI 数据。

#### 文件名行为

当 `filename` 已连接:

```text
sample.png -> output/sample.png
sub/sample.png + path=cleaned -> output/cleaned/sub/sample.png
```

相同路径的已有文件会被覆盖。

当 `filename` 未连接:

```text
空 filename -> output/0001.png, output/0002.png
anima -> output/anima_0001.png, output/anima_0002.png
%date:yyyy-MM-dd%/anima -> output/2026-06-07/anima_0001.png
```

自动递增模式不会覆盖已有文件。

### 文件夹工作流示例

假设上传的文件夹包含:

```text
DatasetRoot/dataset/sample1.png
DatasetRoot/dataset/sample2.png
```

当 `Easy Load Images From Folder` 的 `folder=DatasetRoot` 时，`relative_path` 会输出:

```text
dataset/sample1.png
dataset/sample2.png
```

把 `relative_path` 连接到 Easy Save Image 的 `filename` 后会保存为:

```text
output/dataset/sample1.png
output/dataset/sample2.png
```

如果 `path_enabled=True`, `path=cleaned`，则保存为:

```text
output/cleaned/dataset/sample1.png
output/cleaned/dataset/sample2.png
```
