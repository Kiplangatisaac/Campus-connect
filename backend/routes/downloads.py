from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
import os

router = APIRouter(prefix="/api/downloads", tags=["Downloads"])

# Base paths - resolve relative to the Smartcode-C root
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.normpath(os.path.join(_HERE, "..", "..", ".."))
DEPLOY_DIR = os.path.join(_ROOT, "deploy")
BUILD_DIR = os.path.join(_ROOT, "build")

@router.get("/android")
async def download_android():
    """Download Android APK"""
    apk_path = os.path.join(DEPLOY_DIR, "android", "campus-connect.apk")
    if os.path.exists(apk_path):
        return FileResponse(
            apk_path,
            media_type="application/vnd.android.package-archive",
            filename="KyU-CampusConnect.apk",
            headers={"Content-Disposition": "attachment; filename=KyU-CampusConnect.apk"}
        )
    return RedirectResponse(
        url="https://github.com/Kiplangatisaac/Campus-connect/releases",
        status_code=302
    )

@router.get("/windows")
async def download_windows():
    """Download Windows installer"""
    exe_path = os.path.join(DEPLOY_DIR, "windows", "campus-connect-setup.exe")
    if os.path.exists(exe_path):
        return FileResponse(
            exe_path,
            media_type="application/octet-stream",
            filename="KyU-CampusConnect-Setup.exe",
            headers={"Content-Disposition": "attachment; filename=KyU-CampusConnect-Setup.exe"}
        )
    return RedirectResponse(
        url="https://github.com/Kiplangatisaac/Campus-connect/releases",
        status_code=302
    )

@router.get("/linux")
async def download_linux():
    """Download Linux DEB package"""
    deb_path = os.path.join(DEPLOY_DIR, "linux", "build", "campus-connect_1.0.0_amd64.deb")
    if os.path.exists(deb_path):
        return FileResponse(
            deb_path,
            media_type="application/vnd.debian.binary-package",
            filename="KyU-CampusConnect.deb",
            headers={"Content-Disposition": "attachment; filename=KyU-CampusConnect.deb"}
        )
    # Redirect to GitHub releases
    return RedirectResponse(
        url="https://github.com/Kiplangatisaac/Campus-connect/releases",
        status_code=302
    )

@router.get("/appimage")
async def download_appimage():
    """Download Linux AppImage"""
    appimage_path = os.path.join(DEPLOY_DIR, "linux", "appimage", "KyU-CampusConnect.AppImage")
    if os.path.exists(appimage_path):
        return FileResponse(
            appimage_path,
            media_type="application/x-appimage",
            filename="KyU-CampusConnect.AppImage",
            headers={"Content-Disposition": "attachment; filename=KyU-CampusConnect.AppImage"}
        )
    return RedirectResponse(
        url="https://github.com/Kiplangatisaac/Campus-connect/releases",
        status_code=302
    )

@router.get("/info")
async def download_info():
    """Get download information for all platforms"""
    return {
        "platforms": [
            {
                "id": "android",
                "name": "Android",
                "icon": "📱",
                "description": "Install on your Android device",
                "fileSize": "~15 MB",
                "format": "APK",
                "downloadUrl": "/api/downloads/android",
                "minVersion": "Android 6.0+",
                "version": "1.0.0",
            },
            {
                "id": "windows",
                "name": "Windows",
                "icon": "💻",
                "description": "Install on your Windows PC",
                "fileSize": "~25 MB",
                "format": "EXE",
                "downloadUrl": "/api/downloads/windows",
                "minVersion": "Windows 10+",
                "version": "1.0.0",
            },
            {
                "id": "linux",
                "name": "Linux",
                "icon": "🐧",
                "description": "Install on your Linux system",
                "fileSize": "~12 MB",
                "format": "DEB",
                "downloadUrl": "/api/downloads/linux",
                "minVersion": "Ubuntu 20.04+",
                "version": "1.0.0",
            },
            {
                "id": "appimage",
                "name": "Linux AppImage",
                "icon": "📦",
                "description": "Portable Linux app",
                "fileSize": "~50 MB",
                "format": "AppImage",
                "downloadUrl": "/api/downloads/appimage",
                "minVersion": "Any Linux",
                "version": "1.0.0",
            },
            {
                "id": "web",
                "name": "Web App (PWA)",
                "icon": "🌐",
                "description": "Add to home screen",
                "fileSize": "N/A",
                "format": "PWA",
                "downloadUrl": None,
                "minVersion": "Any browser",
                "version": "1.0.0",
            },
        ],
        "latestVersion": "1.0.0",
        "releaseDate": "2026-07-13",
        "releaseNotes": "Initial release with full OOD architecture",
    }
