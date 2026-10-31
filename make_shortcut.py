import os
import subprocess
import tempfile

def create_desktop_shortcut():
    desktop = os.path.expanduser("~/Desktop")
    target = os.path.abspath("dist/Scriber/Scriber.exe").replace(r"\criber\dist", r"\scriber\dist").replace("/criber/dist", "/scriber/dist")
    icon = os.path.abspath("scriber/assets/icon.ico").replace(r"\criber\scriber", r"\scriber\scriber").replace("/criber/scriber", "/scriber/scriber")
    workdir = os.path.abspath("dist/Scriber").replace(r"\criber\dist", r"\scriber\dist").replace("/criber/dist", "/scriber/dist")
    lnk_path = os.path.join(desktop, "Scriber.lnk")

    vbs_content = f'''Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{lnk_path}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{target}"
oLink.WorkingDirectory = "{workdir}"
oLink.Description = "Scriber Studio"
oLink.IconLocation = "{icon},0"
oLink.Save
'''
    with tempfile.NamedTemporaryFile("w", suffix=".vbs", delete=False) as f:
        f.write(vbs_content)
        tmp_vbs = f.name

    try:
        subprocess.run(["cscript", "//nologo", tmp_vbs], check=True)
        print("Successfully created shortcut at:", lnk_path)
    finally:
        if os.path.exists(tmp_vbs):
            os.remove(tmp_vbs)

if __name__ == "__main__":
    create_desktop_shortcut()
