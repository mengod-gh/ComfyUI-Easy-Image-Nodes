from .nodes import (
    EasyImageNodesLoadImage,
    EasyImageNodesLoadImagesFromFolder,
    EasyImageNodesSaveImage,
)

NODE_CLASS_MAPPINGS = {
    "EasyImageNodes_LoadImage": EasyImageNodesLoadImage,
    "EasyImageNodes_LoadImagesFromFolder": EasyImageNodesLoadImagesFromFolder,
    "EasyImageNodes_SaveImage": EasyImageNodesSaveImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EasyImageNodes_LoadImage": "Easy Load Image",
    "EasyImageNodes_LoadImagesFromFolder": "Easy Load Images From Folder",
    "EasyImageNodes_SaveImage": "Easy Save Image",
}

WEB_DIRECTORY = "./web"

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
