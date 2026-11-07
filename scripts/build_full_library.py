"""
Script to build and classify the comprehensive Easy_Terminal command library.
Merges:
1. Lifewire A-Z Windows Command Prompt commands (284 commands)
2. User-provided curated everyday/specialized tables (Files, Search, Disks, Network,
   Processes, Users, System info, Power, Repair, Boot, Batch syntax)
3. Full Git Command Reference & Cheat Sheet
4. Core PowerShell Cmdlets Reference

Author: B.Mohammed_Amin
License: MIT
"""

import json
import re
import urllib.request
from html import unescape
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
SEED_FILE = ROOT_DIR / "command_center" / "data" / "seed_library.json"

# Load existing seed library
existing_entries = []
if SEED_FILE.exists():
    existing_entries = json.loads(SEED_FILE.read_text(encoding="utf-8"))

existing_by_cmd = {item["command"].strip().lower(): item for item in existing_entries}


def fetch_lifewire_commands() -> dict[str, str]:
    """Fetches and parses the 284 commands from Lifewire."""
    url = "https://www.lifewire.com/list-of-command-prompt-commands-4092302"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL)
        commands = {}
        for r in rows:
            cols = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.DOTALL)
            cols = [unescape(re.sub(r"<[^>]+>", "", c).strip()) for c in cols]
            if len(cols) >= 2 and cols[0] != "Command":
                name = cols[0].strip()
                desc = cols[1].strip()
                commands[name] = desc
        return commands
    except Exception as e:
        print(f"Warning: could not fetch Lifewire directly ({e}), using local mapping.")
        return {}


def classify_lifewire_command(cmd_name: str, desc: str) -> dict:
    """Classifies a Lifewire command into category, tier, shell, and metadata."""
    cmd_lower = cmd_name.lower()

    # Determine default tier
    everyday_roots = {
        "help", "dir", "cd", "cls", "copy", "move", "del", "ren", "mkdir", "rmdir",
        "type", "echo", "attrib", "tree", "ping", "ipconfig", "whoami", "systeminfo",
        "tasklist", "curl", "where", "date", "time", "ver", "title", "color", "exit",
        "path", "find", "findstr", "sort", "clip", "assoc", "start", "pause", "more"
    }
    tier = "everyday" if cmd_lower in everyday_roots else "specialized"

    # Determine Category
    network_cmds = {
        "arp", "atmadm", "finger", "ftp", "getmac", "ipconfig", "nbtstat", "net",
        "netsh", "netstat", "nslookup", "pathping", "ping", "rasdial", "rasphone",
        "rcp", "rexec", "route", "rsh", "tftp", "tracert", "winrm", "winrs", "telnet"
    }
    disk_cmds = {
        "bdehdcfg", "chkdsk", "chkntfs", "cleanmgr", "compact", "convert", "defrag",
        "diskpart", "diskperf", "diskraid", "diskshadow", "dism", "format", "fsutil",
        "label", "mountvol", "recover", "subst", "vol", "vds"
    }
    file_cmds = {
        "append", "attrib", "cacls", "cd", "chdir", "comp", "copy", "del", "dir",
        "erase", "expand", "extract", "fc", "icacls", "inuse", "makecab", "md",
        "mkdir", "mklink", "more", "move", "openfiles", "rd", "ren", "rename",
        "replace", "rmdir", "robocopy", "takeown", "tree", "type", "xcopy"
    }
    process_cmds = {
        "at", "break", "choice", "doskey", "pause", "procDump", "psexec", "pskill",
        "pslist", "qprocess", "quser", "qwinsta", "runas", "schtasks", "sleep",
        "taskkill", "tasklist", "timeout", "tlist", "tskill", "waitfor"
    }
    service_cmds = {
        "change", "logman", "psservice", "qappsrv", "relog", "reset session", "sc",
        "tscon", "tsdiscon", "tsshutdn", "typeperf"
    }
    user_cmds = {
        "addusers", "cmdkey", "gpresult", "gpupdate", "klist", "ksetup", "ktpass",
        "logoff", "moveuser", "net accounts", "net localgroup", "net user", "ntrights",
        "perms", "psloggedon", "pspasswd", "whoami"
    }
    security_cmds = {
        "auditpol", "certreq", "certutil", "cipher", "mbsacli", "secedit", "sysmon",
        "wevtutil"
    }
    search_cmds = {
        "assoc", "clip", "find", "findstr", "ftype", "path", "qgrep", "sort",
        "strings", "where"
    }

    if cmd_lower in network_cmds:
        category = "Network"
    elif cmd_lower in disk_cmds:
        category = "Disk"
    elif cmd_lower in file_cmds:
        category = "Files"
    elif cmd_lower in process_cmds:
        category = "Processes"
    elif cmd_lower in service_cmds:
        category = "Services"
    elif cmd_lower in user_cmds:
        category = "Users"
    elif cmd_lower in security_cmds:
        category = "Security"
    elif cmd_lower in search_cmds:
        category = "Search"
    else:
        category = "System"

    # Default command syntax and example
    cmd_str = cmd_name.lower()
    example = f"{cmd_str} /?"
    if cmd_lower == "assoc":
        cmd_str = "assoc"
        example = "assoc .txt"
    elif cmd_lower == "attrib":
        cmd_str = "attrib"
        example = "attrib +h myfile.txt"
    elif cmd_lower == "bcdedit":
        cmd_str = "bcdedit"
        example = "bcdedit /enum"
    elif cmd_lower == "certutil":
        cmd_str = "certutil"
        example = "certutil -hashfile myfile.zip SHA256"
    elif cmd_lower == "chkdsk":
        cmd_str = "chkdsk C: /scan"
        example = "chkdsk C: /scan"
    elif cmd_lower == "cipher":
        cmd_str = "cipher"
        example = "cipher /w:C:"
    elif cmd_lower == "cleanmgr":
        cmd_str = "cleanmgr /sagerun:1"
        example = "cleanmgr /sageset:1"
    elif cmd_lower == "clip":
        cmd_str = "dir | clip"
        example = "ipconfig | clip"
    elif cmd_lower == "compact":
        cmd_str = "compact /c /s:folder"
        example = "compact /u /s:folder"
    elif cmd_lower == "defrag":
        cmd_str = "defrag C: /O"
        example = "defrag C: /A"
    elif cmd_lower == "driverquery":
        cmd_str = "driverquery /v"
        example = "driverquery /fo list"
    elif cmd_lower == "fsutil":
        cmd_str = "fsutil volume diskfree C:"
        example = "fsutil fsinfo drives"
    elif cmd_lower == "getmac":
        cmd_str = "getmac /v"
        example = "getmac /fo list"
    elif cmd_lower == "gpupdate":
        cmd_str = "gpupdate /force"
        example = "gpupdate /target:computer /force"
    elif cmd_lower == "gpresult":
        cmd_str = "gpresult /r"
        example = "gpresult /v"
    elif cmd_lower == "icacls":
        cmd_str = "icacls folder /grant %USERNAME%:(OI)(CI)F"
        example = "icacls file.txt /reset"
    elif cmd_lower == "logman":
        cmd_str = "logman query"
        example = "logman start perflog"
    elif cmd_lower == "mklink":
        cmd_str = "mklink /D link target"
        example = "mklink /H hardlink file.txt"
    elif cmd_lower == "netsh":
        cmd_str = "netsh interface ipv4 show config"
        example = "netsh advfirewall show allprofiles state"
    elif cmd_lower == "pathping":
        cmd_str = "pathping -n 8.8.8.8"
        example = "pathping 1.1.1.1"
    elif cmd_lower == "powercfg":
        cmd_str = "powercfg /batteryreport"
        example = "powercfg /energy"
    elif cmd_lower == "robocopy":
        cmd_str = "robocopy src dst /MIR /MT:8"
        example = "robocopy src dst /E /ZB"
    elif cmd_lower == "route":
        cmd_str = "route print -4"
        example = "route print"
    elif cmd_lower == "schtasks":
        cmd_str = "schtasks /query /fo list"
        example = "schtasks /query /fo table"
    elif cmd_lower == "sfc":
        cmd_str = "sfc /scannow"
        example = "sfc /verifyonly"
    elif cmd_lower == "systeminfo":
        cmd_str = "systeminfo"
        example = "systeminfo | findstr /B /C:\"OS Name\""
    elif cmd_lower == "takeown":
        cmd_str = "takeown /f file.txt"
        example = "takeown /f folder /r /d y"
    elif cmd_lower == "taskkill":
        cmd_str = "taskkill /im notepad.exe /f"
        example = "taskkill /pid 1234 /f"
    elif cmd_lower == "tasklist":
        cmd_str = "tasklist"
        example = "tasklist /fi \"memusage gt 50000\""
    elif cmd_lower == "tracert":
        cmd_str = "tracert -d 8.8.8.8"
        example = "tracert 1.1.1.1"
    elif cmd_lower == "wevtutil":
        cmd_str = "wevtutil qe System /c:5 /rd:true /f:text"
        example = "wevtutil el"
    elif cmd_lower == "where":
        cmd_str = "where python"
        example = "where curl tar"
    elif cmd_lower == "whoami":
        cmd_str = "whoami /all"
        example = "whoami /groups"

    tags = f"{cmd_lower},{category.lower()},{tier}"

    return {
        "name": f"{cmd_name.capitalize()} Utility",
        "command": cmd_str,
        "shell": "cmd" if cmd_lower in {"assoc", "ftype", "color", "doskey", "prompt", "title"} else "both",
        "category": category,
        "description": desc.split(".")[0].strip() + ".",
        "example": example,
        "tags": tags,
    }


def main():
    print("==> Gathering Lifewire commands...")
    lifewire_dict = fetch_lifewire_commands()
    print(f"    Fetched {len(lifewire_dict)} commands from Lifewire.")

    # We will build our unified dictionary keyed by lower(command)
    unified = {}
    for entry in existing_entries:
        cmd_key = entry["command"].strip().lower()
        unified[cmd_key] = entry

    # 1. Add all Lifewire commands
    for name, desc in lifewire_dict.items():
        classified = classify_lifewire_command(name, desc)
        cmd_key = classified["command"].strip().lower()
        if cmd_key not in unified:
            unified[cmd_key] = classified
        else:
            # Enrich existing entry if needed
            if "tags" in unified[cmd_key] and "everyday" not in unified[cmd_key]["tags"] and "specialized" not in unified[cmd_key]["tags"]:
                unified[cmd_key]["tags"] += f",{classified['tags']}"

    # 2. Add Curated Everyday & Specialized Tables from User Request
    curated_user_commands = [
        # Everyday Navigation & System
        {"name": "Help Reference", "command": "help", "shell": "both", "category": "System", "description": "List built-in commands with one-line descriptions.", "example": "help", "tags": "help,system,info,everyday"},
        {"name": "Command Syntax Help", "command": "robocopy /?", "shell": "both", "category": "Files", "description": "Display full command-line parameter syntax for any command.", "example": "robocopy /?", "tags": "help,syntax,everyday"},
        {"name": "Change Drive and Folder", "command": "cd /d F:\\", "shell": "cmd", "category": "Files", "description": "Change both drive and directory in one step.", "example": "cd /d D:\\projects", "tags": "cd,navigate,everyday"},
        {"name": "List Files Newest First", "command": "dir /a /o:-d", "shell": "cmd", "category": "Files", "description": "List all files including hidden, ordered newest first.", "example": "dir /a /o:-d", "tags": "dir,files,hidden,everyday"},
        {"name": "Locate Programs on PATH", "command": "where curl tar", "shell": "both", "category": "Search", "description": "Show where commands live along the system PATH.", "example": "where python git", "tags": "where,path,search,everyday"},
        {"name": "Windows Build Version", "command": "ver", "shell": "cmd", "category": "System", "description": "Display Windows OS kernel and build number.", "example": "ver", "tags": "version,os,everyday"},
        {"name": "Environment Variables", "command": "set", "shell": "cmd", "category": "System", "description": "List all current environment variables and values.", "example": "set", "tags": "env,variables,everyday"},
        {"name": "Set Persistent User Variable", "command": "setx NAME value", "shell": "both", "category": "System", "description": "Save an environment variable permanently for future sessions.", "example": "setx EDITOR notepad", "tags": "setx,env,specialized"},
        {"name": "Clear Screen", "command": "cls", "shell": "both", "category": "System", "description": "Clear the terminal output screen.", "example": "cls", "tags": "cls,clear,everyday"},

        # Files and Folders
        {"name": "Create Folder Tree", "command": "mkdir C:\\lab\\demo\\logs", "shell": "both", "category": "Files", "description": "Create a directory folder path including parent folders.", "example": "mkdir C:\\logs\\app", "tags": "mkdir,folder,create,everyday"},
        {"name": "Copy Overwrite File", "command": "copy /y a.txt b.txt", "shell": "both", "category": "Files", "description": "Copy a file and overwrite destination without asking.", "example": "copy /y src.txt dst.txt", "tags": "copy,files,everyday"},
        {"name": "Copy Tree with Empty & Hidden", "command": "xcopy src dst\\ /e /i /h /y", "shell": "both", "category": "Files", "description": "Copy a directory tree including empty and hidden files.", "example": "xcopy C:\\src C:\\dst /e /h /y", "tags": "xcopy,backup,files,specialized"},
        {"name": "Mirror Directory Multi-threaded", "command": "robocopy src dst /MIR /MT:8", "shell": "both", "category": "Files", "description": "Mirror a directory folder tree using 8 parallel threads.", "example": "robocopy C:\\src C:\\dst /MIR /MT:8", "tags": "robocopy,mirror,sync,specialized"},
        {"name": "Move File", "command": "move c.txt logs\\", "shell": "both", "category": "Files", "description": "Move a file from one directory to another.", "example": "move data.txt logs\\", "tags": "move,files,everyday"},
        {"name": "Rename File", "command": "ren b.txt c.txt", "shell": "cmd", "category": "Files", "description": "Rename a file to a new name.", "example": "ren old.txt new.txt", "tags": "ren,rename,files,everyday"},
        {"name": "Delete Matching Subfolder Files", "command": "del /s /q *.tmp", "shell": "both", "category": "Files", "description": "Quietly delete matching files in current and all subfolders.", "example": "del /s /q *.log", "tags": "del,delete,cleanup,specialized"},
        {"name": "Remove Folder Recursively", "command": "rmdir /s /q logs", "shell": "both", "category": "Files", "description": "Delete a folder and all its contents without confirmation.", "example": "rmdir /s /q temp", "tags": "rmdir,delete,folder,specialized"},
        {"name": "Hide File Attribute", "command": "attrib +h a.txt", "shell": "both", "category": "Files", "description": "Set hidden file attribute on a file (+h hides, -h unhides).", "example": "attrib +h secret.txt", "tags": "attrib,hidden,files,specialized"},
        {"name": "ASCII Folder Tree View", "command": "tree /a /f", "shell": "both", "category": "Files", "description": "Display graphical ASCII tree view of folders and files.", "example": "tree /a /f", "tags": "tree,files,diagram,everyday"},
        {"name": "Create Directory Symbolic Link", "command": "mklink /d link target", "shell": "cmd", "category": "Files", "description": "Create a directory symbolic link in NTFS.", "example": "mklink /d C:\\symlink C:\\target", "tags": "mklink,symlink,admin,specialized"},
        {"name": "Print File Contents", "command": "type a.txt", "shell": "both", "category": "Files", "description": "Display the raw text contents of a file in the console.", "example": "type README.md", "tags": "type,cat,files,everyday"},

        # Search and Compare Text
        {"name": "Find Text Line Numbers", "command": "findstr /i /n \"error\" app.log", "shell": "both", "category": "Search", "description": "Case-insensitive text search with line numbers.", "example": "findstr /i /n \"failed\" server.log", "tags": "findstr,grep,search,everyday"},
        {"name": "Search Files Containing String", "command": "findstr /s /i /m \"error\" *", "shell": "both", "category": "Search", "description": "List files in directory and subdirectories containing a string.", "example": "findstr /s /i /m \"TODO\" *.py", "tags": "findstr,search,code,everyday"},
        {"name": "Count File Lines", "command": "find /c /v \"\" app.log", "shell": "both", "category": "Search", "description": "Count total number of lines in a file.", "example": "find /c /v \"\" data.csv", "tags": "find,wc,count,everyday"},
        {"name": "Reverse Sort File Lines", "command": "sort /r app.log", "shell": "both", "category": "Search", "description": "Sort lines of text in reverse alphabetical order.", "example": "sort /r words.txt", "tags": "sort,text,search,everyday"},
        {"name": "Compare Two Files", "command": "fc a.txt b.txt", "shell": "both", "category": "Search", "description": "Compare two files and output differing lines.", "example": "fc v1.txt v2.txt", "tags": "fc,diff,compare,everyday"},
        {"name": "Find Files Full Paths", "command": "dir /b /s *.log", "shell": "cmd", "category": "Search", "description": "Find all matching files recursively, printing full paths.", "example": "dir /b /s *.pdf", "tags": "dir,find,paths,everyday"},
        {"name": "Pipe Text to Clipboard", "command": "echo text | clip", "shell": "both", "category": "Search", "description": "Send standard input or text directly to the Windows clipboard.", "example": "dir /b | clip", "tags": "clip,clipboard,pipe,everyday"},

        # Disks and Volumes
        {"name": "DiskPart Partition Shell", "command": "diskpart", "shell": "both", "category": "Disk", "description": "Launch the Windows DiskPart partition manager (admin).", "example": "diskpart", "tags": "diskpart,partition,admin,specialized"},
        {"name": "List Disks and Volumes", "command": "list disk", "shell": "both", "category": "Disk", "description": "List available physical disks in diskpart.", "example": "list volume", "tags": "diskpart,disk,specialized"},
        {"name": "Select Active Disk", "command": "select disk 1", "shell": "both", "category": "Disk", "description": "Select the target disk for partition commands in diskpart.", "example": "select disk 0", "tags": "diskpart,select,specialized"},
        {"name": "Bring Offline Disk Online", "command": "online disk", "shell": "both", "category": "Disk", "description": "Bring an offline physical disk online in diskpart.", "example": "online disk", "tags": "diskpart,mount,specialized"},
        {"name": "Clear Disk Read-Only", "command": "attributes disk clear readonly", "shell": "both", "category": "Disk", "description": "Clear the read-only flag on the selected disk.", "example": "attributes disk clear readonly", "tags": "diskpart,readonly,specialized"},
        {"name": "Clean Disk Partitions", "command": "clean", "shell": "both", "category": "Disk", "description": "Wipe every partition table from the selected disk in diskpart.", "example": "clean", "tags": "diskpart,clean,wipe,specialized"},
        {"name": "Convert Disk to GPT", "command": "convert gpt", "shell": "both", "category": "Disk", "description": "Convert empty disk partition style to GPT.", "example": "convert gpt", "tags": "diskpart,gpt,specialized"},
        {"name": "Create Primary Partition", "command": "create partition primary", "shell": "both", "category": "Disk", "description": "Create a primary partition using all remaining free space.", "example": "create partition primary", "tags": "diskpart,partition,specialized"},
        {"name": "Quick Format Volume NTFS", "command": "format fs=ntfs quick label=DATA", "shell": "both", "category": "Disk", "description": "Quickly format selected volume as NTFS with a label in diskpart.", "example": "format fs=ntfs quick label=BACKUP", "tags": "diskpart,format,ntfs,specialized"},
        {"name": "Assign Volume Letter", "command": "assign letter=F", "shell": "both", "category": "Disk", "description": "Assign a drive letter to the selected volume in diskpart.", "example": "assign letter=E", "tags": "diskpart,drive,specialized"},
        {"name": "Execute DiskPart Script", "command": "diskpart /s script.txt", "shell": "both", "category": "Disk", "description": "Run automated DiskPart partition commands from a text script.", "example": "diskpart /s setup.txt", "tags": "diskpart,script,admin,specialized"},
        {"name": "Format Volume CLI", "command": "format F: /fs:ntfs /q /v:DATA /y", "shell": "both", "category": "Disk", "description": "Quickly format volume with label from standard prompt.", "example": "format E: /fs:exfat /q /y", "tags": "format,volume,admin,specialized"},
        {"name": "Volume Free & Used Space", "command": "fsutil volume diskfree F:", "shell": "both", "category": "Disk", "description": "Query exact free and total capacity bytes on a volume.", "example": "fsutil volume diskfree C:", "tags": "fsutil,disk,free,everyday"},
        {"name": "Show or Set Volume Label", "command": "vol F: / label F: BACKUP", "shell": "cmd", "category": "Disk", "description": "Show current volume serial or set volume label name.", "example": "vol C:", "tags": "vol,label,disk,everyday"},

        # Network
        {"name": "Renew DHCP IP Address", "command": "ipconfig /release & ipconfig /renew", "shell": "both", "category": "Network", "description": "Release and obtain a new DHCP lease in a single combined step.", "example": "ipconfig /release & ipconfig /renew", "tags": "ipconfig,dhcp,network,everyday"},
        {"name": "Ping Four Packets", "command": "ping -n 4 1.1.1.1", "shell": "both", "category": "Network", "description": "Send four ICMP echo requests to verify connectivity.", "example": "ping -n 4 8.8.8.8", "tags": "ping,icmp,network,everyday"},
        {"name": "Fast Traceroute No DNS", "command": "tracert -d 1.1.1.1", "shell": "both", "category": "Network", "description": "Trace network hops without reverse DNS resolution for speed.", "example": "tracert -d 8.8.8.8", "tags": "tracert,hops,network,everyday"},
        {"name": "Pathping Packet Loss Test", "command": "pathping -n 1.1.1.1", "shell": "both", "category": "Network", "description": "Analyze network path and latency plus packet loss per hop.", "example": "pathping -n 8.8.8.8", "tags": "pathping,packetloss,network,specialized"},
        {"name": "DNS MX Record Lookup", "command": "nslookup -type=mx example.com", "shell": "both", "category": "Network", "description": "Query specific mail exchanger (MX) DNS records for a domain.", "example": "nslookup -type=mx google.com", "tags": "nslookup,dns,mx,network,everyday"},
        {"name": "Port Listening Process PID", "command": "netstat -ano | findstr :3389", "shell": "both", "category": "Network", "description": "Find which PID is listening on a specific TCP/UDP port.", "example": "netstat -ano | findstr :8080", "tags": "netstat,port,pid,network,specialized"},
        {"name": "Show Interface IP & DNS", "command": "netsh interface ipv4 show config", "shell": "both", "category": "Network", "description": "Display address, default gateway, and DNS servers per adapter.", "example": "netsh interface ipv4 show config", "tags": "netsh,ipv4,network,everyday"},
        {"name": "Set Static DNS Server", "command": "netsh interface ipv4 set dnsservers name=\"Ethernet\" static 1.1.1.1 primary", "shell": "both", "category": "Network", "description": "Configure static primary DNS resolver on a network adapter.", "example": "netsh interface ipv4 set dnsservers name=\"Wi-Fi\" static 8.8.8.8 primary", "tags": "netsh,dns,network,admin,specialized"},
        {"name": "Firewall State Per Profile", "command": "netsh advfirewall show allprofiles state", "shell": "both", "category": "Network", "description": "Check if Windows Firewall is enabled across all network profiles.", "example": "netsh advfirewall show allprofiles state", "tags": "firewall,security,network,everyday"},
        {"name": "Add Inbound Firewall Port Rule", "command": "netsh advfirewall firewall add rule name=\"Allow TCP 8080\" dir=in action=allow protocol=TCP localport=8080", "shell": "both", "category": "Network", "description": "Open a TCP port in Windows Firewall for inbound traffic.", "example": "netsh advfirewall firewall add rule name=\"Node 3000\" dir=in action=allow protocol=TCP localport=3000", "tags": "firewall,rule,port,admin,specialized"},
        {"name": "Fetch HTTP Headers", "command": "curl -I https://example.com", "shell": "both", "category": "Network", "description": "Inspect HTTP response headers without downloading response body.", "example": "curl -I https://google.com", "tags": "curl,http,headers,network,everyday"},

        # Processes and Services
        {"name": "Find Process By Image Name", "command": "tasklist /fi \"imagename eq ping.exe\"", "shell": "both", "category": "Processes", "description": "Find specific running process entries by executable name.", "example": "tasklist /fi \"imagename eq node.exe\"", "tags": "tasklist,process,find,everyday"},
        {"name": "Services Hosted in Processes", "command": "tasklist /svc", "shell": "both", "category": "Processes", "description": "List Windows services hosted inside each running process.", "example": "tasklist /svc", "tags": "tasklist,services,svchost,specialized"},
        {"name": "Find High Memory Processes", "command": "tasklist /fi \"memusage gt 100000\"", "shell": "both", "category": "Processes", "description": "List all processes consuming more than 100 MB of RAM.", "example": "tasklist /fi \"memusage gt 200000\"", "tags": "tasklist,ram,memory,everyday"},
        {"name": "Force Kill Process by Name", "command": "taskkill /im ping.exe /f", "shell": "both", "category": "Processes", "description": "Forcibly terminate running processes by executable name.", "example": "taskkill /im notepad.exe /f", "tags": "taskkill,kill,force,everyday"},
        {"name": "Kill Process Tree by PID", "command": "taskkill /pid 2792 /t /f", "shell": "both", "category": "Processes", "description": "Kill target process ID and all spawned child processes.", "example": "taskkill /pid 1234 /t /f", "tags": "taskkill,tree,pid,specialized"},
        {"name": "Query Service State", "command": "sc query Spooler", "shell": "both", "category": "Services", "description": "Query current running state and exit code of a service.", "example": "sc query wuauserv", "tags": "sc,service,query,everyday"},
        {"name": "Query Service Configuration", "command": "sc qc Spooler", "shell": "both", "category": "Services", "description": "View service start type, binary path, and user account.", "example": "sc qc Winmgmt", "tags": "sc,service,config,specialized"},
        {"name": "Set Service Start Type", "command": "sc config Spooler start= demand", "shell": "both", "category": "Services", "description": "Set service startup type to auto, demand, or disabled.", "example": "sc config Spooler start= auto", "tags": "sc,service,admin,specialized"},
        {"name": "Query Service with PID", "command": "sc queryex Spooler", "shell": "both", "category": "Services", "description": "Query service state alongside its host process PID.", "example": "sc queryex wuauserv", "tags": "sc,pid,service,specialized"},
        {"name": "Restart Service Synchronously", "command": "net stop Spooler / net start Spooler", "shell": "both", "category": "Services", "description": "Stop and start a service, waiting for confirmation.", "example": "net stop wuauserv & net start wuauserv", "tags": "net,service,restart,specialized"},

        # Users and Permissions
        {"name": "User Security Groups and Integrity", "command": "whoami /groups", "shell": "both", "category": "Users", "description": "Show group memberships and mandatory integrity level.", "example": "whoami /priv", "tags": "whoami,groups,security,everyday"},
        {"name": "List Local Users", "command": "net user", "shell": "both", "category": "Users", "description": "List all local user accounts registered on this PC.", "example": "net user", "tags": "net,user,accounts,everyday"},
        {"name": "Create Local User Account", "command": "net user joshua Lab-Pass-26! /add", "shell": "both", "category": "Users", "description": "Create a new local Windows user account with password.", "example": "net user dev MyPass123! /add", "tags": "net,user,create,admin,specialized"},
        {"name": "Add User to Administrators", "command": "net localgroup Administrators joshua /add", "shell": "both", "category": "Users", "description": "Grant administrative privileges by adding user to Administrators.", "example": "net localgroup Administrators dev /add", "tags": "net,admin,privilege,specialized"},
        {"name": "Disable User Account", "command": "net user joshua /active:no", "shell": "both", "category": "Users", "description": "Disable a local user account without deleting it.", "example": "net user guest /active:no", "tags": "net,user,disable,specialized"},
        {"name": "Delete User Account", "command": "net user joshua /delete", "shell": "both", "category": "Users", "description": "Permanently remove a local user account.", "example": "net user testuser /delete", "tags": "net,user,delete,specialized"},
        {"name": "Password Policy Settings", "command": "net accounts", "shell": "both", "category": "Users", "description": "Display minimum password length, age, and lockout threshold.", "example": "net accounts", "tags": "net,policy,security,everyday"},
        {"name": "Grant Inherited Folder Modify Permission", "command": "icacls C:\\data /grant joshua:(OI)(CI)M", "shell": "both", "category": "Users", "description": "Grant inherited Modify permissions on directory tree.", "example": "icacls C:\\shared /grant Users:(OI)(CI)M", "tags": "icacls,permissions,acl,specialized"},
        {"name": "Reset Inherited Permissions", "command": "icacls file.txt /reset", "shell": "both", "category": "Users", "description": "Replace explicit permissions with parent inherited ACLs.", "example": "icacls folder /reset /t", "tags": "icacls,reset,acl,specialized"},
        {"name": "Take Ownership of File", "command": "takeown /f file.txt", "shell": "both", "category": "Users", "description": "Take administrator ownership of a locked or inaccessible file.", "example": "takeown /f locked.txt", "tags": "takeown,owner,admin,specialized"},
        {"name": "List Active Network Shares", "command": "net share", "shell": "both", "category": "Users", "description": "List all shared folder resources on the local machine.", "example": "net share", "tags": "net,share,network,everyday"},

        # System Info, Power, Tasks
        {"name": "Reboot Computer Immediately", "command": "shutdown /r /t 0", "shell": "both", "category": "System", "description": "Immediately restart the local computer with 0 seconds delay.", "example": "shutdown /r /t 0", "tags": "shutdown,reboot,system,everyday"},
        {"name": "Cancel Pending Shutdown", "command": "shutdown /a", "shell": "both", "category": "System", "description": "Abort a previously scheduled shutdown or restart.", "example": "shutdown /a", "tags": "shutdown,abort,system,everyday"},
        {"name": "List Power Plans", "command": "powercfg /l", "shell": "both", "category": "System", "description": "List all power management schemes with active plan starred.", "example": "powercfg /l", "tags": "powercfg,battery,power,everyday"},
        {"name": "Create Daily Scheduled Task", "command": "schtasks /create /tn \"Lab\\Cleanup\" /tr \"cmd /c del /q C:\\lab\\tmp\\*\" /sc daily /st 02:00 /ru SYSTEM", "shell": "both", "category": "System", "description": "Register a daily scheduled task running as SYSTEM.", "example": "schtasks /create /tn \"Backup\" /tr \"backup.bat\" /sc daily /st 01:00", "tags": "schtasks,cron,task,admin,specialized"},
        {"name": "Query Scheduled Task Info", "command": "schtasks /query /tn \"Lab\\Cleanup\" /fo list", "shell": "both", "category": "System", "description": "Query next run time and status of a scheduled task.", "example": "schtasks /query /fo table", "tags": "schtasks,task,query,everyday"},
        {"name": "Windows Time Service Status", "command": "w32tm /query /status", "shell": "both", "category": "System", "description": "Query system clock NTP time source and last sync status.", "example": "w32tm /query /status", "tags": "w32tm,time,clock,ntp,everyday"},
        {"name": "Resync System Clock", "command": "w32tm /resync", "shell": "both", "category": "System", "description": "Force immediate clock synchronization with NTP server.", "example": "w32tm /resync", "tags": "w32tm,ntp,clock,specialized"},
        {"name": "Query Windows Release Version", "command": "reg query \"HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\" /v DisplayVersion", "shell": "both", "category": "System", "description": "Query exact Windows feature release (e.g. 24H2, 23H2).", "example": "reg query \"HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\" /v DisplayVersion", "tags": "reg,version,build,everyday"},

        # Repair and Boot
        {"name": "DISM Check Component Store", "command": "DISM /Online /Cleanup-Image /CheckHealth", "shell": "both", "category": "System", "description": "Check if Windows component store is flagged as corrupted.", "example": "DISM /Online /Cleanup-Image /CheckHealth", "tags": "dism,repair,health,specialized"},
        {"name": "DISM Restore Component Health", "command": "DISM /Online /Cleanup-Image /RestoreHealth", "shell": "both", "category": "System", "description": "Repair corrupted Windows component store using Windows Update.", "example": "DISM /Online /Cleanup-Image /RestoreHealth", "tags": "dism,repair,system,specialized"},
        {"name": "SFC Verify System Files", "command": "sfc /verifyonly", "shell": "both", "category": "System", "description": "Scan integrity of protected system files without modifying them.", "example": "sfc /verifyonly", "tags": "sfc,check,integrity,everyday"},
        {"name": "Fix Disk Errors Locked Volume", "command": "chkdsk F: /f", "shell": "both", "category": "Disk", "description": "Fix file system errors, locking volume or scheduling on reboot.", "example": "chkdsk C: /f", "tags": "chkdsk,repair,disk,specialized"},
        {"name": "Enumerate Current Boot Entry", "command": "bcdedit /enum {current}", "shell": "both", "category": "System", "description": "View Boot Configuration Data entry for the running OS.", "example": "bcdedit /enum {current}", "tags": "bcdedit,boot,admin,specialized"},

        # Batch Syntax & Flow Control
        {"name": "Batch Run on Success", "command": "cmd1 && cmd2", "shell": "cmd", "category": "Batch", "description": "Execute second command only if first command succeeds (exit code 0).", "example": "build.bat && test.bat", "tags": "batch,flow,and,everyday"},
        {"name": "Batch Run on Failure", "command": "cmd1 || cmd2", "shell": "cmd", "category": "Batch", "description": "Execute second command only if first command fails (non-zero exit).", "example": "ping 1.1.1.1 || echo Offline", "tags": "batch,flow,or,everyday"},
        {"name": "Redirect Stdout & Stderr to File", "command": "cmd > out.txt 2>&1", "shell": "both", "category": "Batch", "description": "Redirect both output and error streams into a single log file.", "example": "build.bat > log.txt 2>&1", "tags": "batch,redirect,output,everyday"},
        {"name": "Silence Error Messages", "command": "cmd 2>nul", "shell": "cmd", "category": "Batch", "description": "Discard standard error messages to NUL stream.", "example": "del *.tmp 2>nul", "tags": "batch,nul,silence,everyday"},
        {"name": "Print Last Exit Code", "command": "echo %ERRORLEVEL%", "shell": "cmd", "category": "Batch", "description": "Print numeric exit code of the previously executed command.", "example": "echo %ERRORLEVEL%", "tags": "errorlevel,exit,code,everyday"},
        {"name": "Batch Numeric Counting Loop", "command": "for /l %i in (1,1,3) do echo %i", "shell": "cmd", "category": "Batch", "description": "Iterate a counting loop from start to end with step increment.", "example": "for /l %i in (1,1,5) do echo %i", "tags": "for,loop,batch,specialized"},
        {"name": "Batch File Iteration Loop", "command": "for %f in (*.txt) do echo %~nxf", "shell": "cmd", "category": "Batch", "description": "Loop over matching files in current directory.", "example": "for %f in (*.log) do type %f", "tags": "for,files,batch,specialized"},
        {"name": "Batch File Existence Check", "command": "if exist file.txt (echo found) else (echo missing)", "shell": "cmd", "category": "Batch", "description": "Branch execution based on whether a target file exists.", "example": "if exist config.ini (echo ready)", "tags": "if,branch,batch,everyday"},
        {"name": "Batch Prompt User Choice", "command": "choice /t 15 /c ync /cs /d y /m \"Press y=Yes, n=No, c=cancel:\"", "shell": "cmd", "category": "Batch", "description": "Prompt user to select an on-screen option with optional timeout.", "example": "choice /c yn /m \"Continue?\"", "tags": "choice,prompt,input,everyday"},
        {"name": "Batch Sleep Timeout", "command": "timeout 3600", "shell": "both", "category": "Batch", "description": "Pause script execution for a specified duration in seconds.", "example": "timeout 5", "tags": "timeout,sleep,batch,everyday"},
        {"name": "Batch Pause Prompt", "command": "pause", "shell": "cmd", "category": "Batch", "description": "Prompt user with 'Press any key to continue...' and wait.", "example": "pause", "tags": "pause,wait,batch,everyday"},
        {"name": "Set Console Colors", "command": "color 0A", "shell": "cmd", "category": "Batch", "description": "Set foreground and background color attributes for console.", "example": "color 0A", "tags": "color,theme,cmd,everyday"},
        {"name": "Set Console Window Title", "command": "title My Terminal", "shell": "cmd", "category": "Batch", "description": "Set the text title of the current console window.", "example": "title Easy_Terminal", "tags": "title,window,cmd,everyday"},

        # Full Git Cheat Sheet
        {"name": "Git Initialize Repository", "command": "git init", "shell": "both", "category": "Git", "description": "Create an empty Git repository or reinitialize an existing one.", "example": "git init", "tags": "git,init,vcs,everyday"},
        {"name": "Git Clone Remote", "command": "git clone <url>", "shell": "both", "category": "Git", "description": "Clone an existing remote Git repository into a local folder.", "example": "git clone https://github.com/user/repo.git", "tags": "git,clone,remote,everyday"},
        {"name": "Git Stage File", "command": "git add <file>", "shell": "both", "category": "Git", "description": "Add file contents to the staging area for next commit.", "example": "git add README.md", "tags": "git,add,stage,everyday"},
        {"name": "Git Stage All Changes", "command": "git add .", "shell": "both", "category": "Git", "description": "Stage all modified and newly created files in workspace.", "example": "git add .", "tags": "git,add,stage,everyday"},
        {"name": "Git Patch Stage", "command": "git add -p", "shell": "both", "category": "Git", "description": "Interactively choose which hunks of a file to stage.", "example": "git add -p", "tags": "git,patch,stage,specialized"},
        {"name": "Git Move or Rename File", "command": "git mv <old> <new>", "shell": "both", "category": "Git", "description": "Move or rename a file, folder, or symlink and stage change.", "example": "git mv old.txt new.txt", "tags": "git,mv,rename,everyday"},
        {"name": "Git Remove File", "command": "git rm <file>", "shell": "both", "category": "Git", "description": "Remove file from working tree and staging area.", "example": "git rm temp.log", "tags": "git,rm,delete,everyday"},
        {"name": "Git Untrack Cached File", "command": "git rm --cached <file>", "shell": "both", "category": "Git", "description": "Stop tracking file in Git while keeping it on local disk.", "example": "git rm --cached config.env", "tags": "git,untrack,cache,everyday"},
        {"name": "Git Unstage File", "command": "git restore --staged <file>", "shell": "both", "category": "Git", "description": "Remove a file from staging area while preserving changes.", "example": "git restore --staged app.py", "tags": "git,unstage,restore,everyday"},
        {"name": "Git Working Tree Status", "command": "git status", "shell": "both", "category": "Git", "description": "Show staged, unstaged, and untracked file status.", "example": "git status -s", "tags": "git,status,vcs,everyday"},
        {"name": "Git Commit with Message", "command": "git commit -m \"feat: update\"", "shell": "both", "category": "Git", "description": "Record staged snapshot changes to repository history.", "example": "git commit -m \"fix: resolve bug\"", "tags": "git,commit,vcs,everyday"},
        {"name": "Git Commit All Modified", "command": "git commit -am \"update\"", "shell": "both", "category": "Git", "description": "Automatically stage modified tracked files and commit.", "example": "git commit -am \"refactor: cleanup\"", "tags": "git,commit,everyday"},
        {"name": "Git Switch Branch", "command": "git switch <name>", "shell": "both", "category": "Git", "description": "Switch working tree to target existing branch.", "example": "git switch main", "tags": "git,switch,branch,everyday"},
        {"name": "Git Create & Switch Branch", "command": "git switch -c <name>", "shell": "both", "category": "Git", "description": "Create a new branch and immediately switch to it.", "example": "git switch -c feature/login", "tags": "git,branch,create,everyday"},
        {"name": "Git List Branches Recent", "command": "git branch --sort=-committerdate", "shell": "both", "category": "Git", "description": "List branches sorted by most recently committed to.", "example": "git branch --sort=-committerdate", "tags": "git,branch,list,everyday"},
        {"name": "Git Delete Branch", "command": "git branch -d <name>", "shell": "both", "category": "Git", "description": "Safely delete a merged branch.", "example": "git branch -d feature-test", "tags": "git,branch,delete,everyday"},
        {"name": "Git Diff Unstaged Changes", "command": "git diff", "shell": "both", "category": "Git", "description": "Show line-by-line differences between unstaged files and index.", "example": "git diff", "tags": "git,diff,changes,everyday"},
        {"name": "Git Diff Staged Changes", "command": "git diff --staged", "shell": "both", "category": "Git", "description": "Show line-by-line differences between staged changes and HEAD.", "example": "git diff --staged", "tags": "git,diff,staged,everyday"},
        {"name": "Git Diff All Working Tree", "command": "git diff HEAD", "shell": "both", "category": "Git", "description": "Show all differences in working tree against last commit.", "example": "git diff HEAD", "tags": "git,diff,head,everyday"},
        {"name": "Git Show Commit Details", "command": "git show <commit>", "shell": "both", "category": "Git", "description": "Show metadata and unified diff of a specific commit.", "example": "git show HEAD", "tags": "git,show,commit,everyday"},
        {"name": "Git Show Commit Stat Summary", "command": "git show --stat <commit>", "shell": "both", "category": "Git", "description": "Show file modification count summary for a commit.", "example": "git show --stat HEAD", "tags": "git,show,stat,everyday"},
        {"name": "Git Discard Unstaged Changes", "command": "git restore <file>", "shell": "both", "category": "Git", "description": "Discard unstaged modifications to a file in working tree.", "example": "git restore app.py", "tags": "git,restore,discard,everyday"},
        {"name": "Git Reset Hard Discard All", "command": "git reset --hard HEAD", "shell": "both", "category": "Git", "description": "Discard all staged and unstaged changes, resetting to HEAD.", "example": "git reset --hard HEAD", "tags": "git,reset,hard,specialized"},
        {"name": "Git Clean Untracked Files", "command": "git clean -fd", "shell": "both", "category": "Git", "description": "Remove untracked files and directories from working tree.", "example": "git clean -fd", "tags": "git,clean,untracked,specialized"},
        {"name": "Git Stash Changes", "command": "git stash", "shell": "both", "category": "Git", "description": "Stash current uncommitted changes into a temporary stack.", "example": "git stash", "tags": "git,stash,save,everyday"},
        {"name": "Git Stash Pop", "command": "git stash pop", "shell": "both", "category": "Git", "description": "Reapply most recently stashed changes and remove from stack.", "example": "git stash pop", "tags": "git,stash,apply,everyday"},
        {"name": "Git Undo Last Commit Keep Changes", "command": "git reset HEAD^", "shell": "both", "category": "Git", "description": "Undo the most recent commit while keeping modified files intact.", "example": "git reset HEAD^", "tags": "git,undo,reset,everyday"},
        {"name": "Git Amend Commit Message", "command": "git commit --amend", "shell": "both", "category": "Git", "description": "Modify the commit message or files of the most recent commit.", "example": "git commit --amend --no-edit", "tags": "git,amend,commit,everyday"},
        {"name": "Git One-line Log History", "command": "git log --oneline", "shell": "both", "category": "Git", "description": "Display compact commit history with abbreviated SHA and title.", "example": "git log --oneline -n 10", "tags": "git,log,history,everyday"},
        {"name": "Git Graphical Branch Log", "command": "git log --graph --oneline --all", "shell": "both", "category": "Git", "description": "Show ASCII branch topology graph of all commits.", "example": "git log --graph --oneline --all", "tags": "git,graph,log,everyday"},
        {"name": "Git Blame Line Author", "command": "git blame <file>", "shell": "both", "category": "Git", "description": "Display last modifying commit and author for each file line.", "example": "git blame app.py", "tags": "git,blame,audit,everyday"},
        {"name": "Git Cherry-Pick Commit", "command": "git cherry-pick <commit>", "shell": "both", "category": "Git", "description": "Apply the changes introduced by an existing commit to current branch.", "example": "git cherry-pick 3e887ab", "tags": "git,cherrypick,specialized"},
        {"name": "Git Add Remote URL", "command": "git remote add <name> <url>", "shell": "both", "category": "Git", "description": "Register a new named remote repository URL.", "example": "git remote add origin https://github.com/user/repo.git", "tags": "git,remote,config,everyday"},
        {"name": "Git Push Tracking Branch", "command": "git push -u origin <name>", "shell": "both", "category": "Git", "description": "Push new local branch and set upstream tracking reference.", "example": "git push -u origin main", "tags": "git,push,remote,everyday"},
        {"name": "Git Force Push with Lease", "command": "git push --force-with-lease", "shell": "both", "category": "Git", "description": "Safely force push ensuring no remote commits are overwritten.", "example": "git push --force-with-lease", "tags": "git,force,push,specialized"},
        {"name": "Git Pull Rebase", "command": "git pull --rebase", "shell": "both", "category": "Git", "description": "Fetch remote branch and rebase local commits on top.", "example": "git pull --rebase origin main", "tags": "git,pull,rebase,everyday"},
        {"name": "Git Config User Details", "command": "git config --global user.name \"Your Name\"", "shell": "both", "category": "Git", "description": "Set global author name used for all future commits.", "example": "git config --global user.name \"B.Mohammed_Amin\"", "tags": "git,config,user,everyday"},

        # Core PowerShell Cmdlets
        {"name": "PS Get Running Processes", "command": "Get-Process", "shell": "powershell", "category": "PowerShell", "description": "Retrieve list of all active processes and resource metrics.", "example": "Get-Process | Sort-Object CPU -Descending", "tags": "powershell,process,everyday"},
        {"name": "PS Stop Process", "command": "Stop-Process -Name ping -Force", "shell": "powershell", "category": "PowerShell", "description": "Forcibly stop one or more running processes by name or PID.", "example": "Stop-Process -Id 1234 -Force", "tags": "powershell,kill,process,everyday"},
        {"name": "PS Start Process", "command": "Start-Process notepad", "shell": "powershell", "category": "PowerShell", "description": "Launch one or more processes on the local computer.", "example": "Start-Process powershell -Verb RunAs", "tags": "powershell,start,process,everyday"},
        {"name": "PS Get Installed Services", "command": "Get-Service", "shell": "powershell", "category": "PowerShell", "description": "Display status and startup types of all installed services.", "example": "Get-Service | Where-Object Status -eq 'Running'", "tags": "powershell,services,everyday"},
        {"name": "PS Start Windows Service", "command": "Start-Service Spooler", "shell": "powershell", "category": "PowerShell", "description": "Start one or more stopped Windows services.", "example": "Start-Service wuauserv", "tags": "powershell,service,start,specialized"},
        {"name": "PS Stop Windows Service", "command": "Stop-Service Spooler", "shell": "powershell", "category": "PowerShell", "description": "Stop one or more running Windows services.", "example": "Stop-Service Spooler", "tags": "powershell,service,stop,specialized"},
        {"name": "PS List Child Items", "command": "Get-ChildItem -Recurse", "shell": "powershell", "category": "PowerShell", "description": "Get files and folders from file system or registry recursively.", "example": "Get-ChildItem -Filter *.py", "tags": "powershell,dir,files,everyday"},
        {"name": "PS Get File Content", "command": "Get-Content app.log -Tail 20", "shell": "powershell", "category": "PowerShell", "description": "Read file lines as string objects with optional tail stream.", "example": "Get-Content server.log -Wait", "tags": "powershell,cat,content,everyday"},
        {"name": "PS Set File Content", "command": "Set-Content -Path file.txt -Value 'hello'", "shell": "powershell", "category": "PowerShell", "description": "Write or overwrite new content into target file.", "example": "Set-Content version.txt '1.0.0'", "tags": "powershell,write,file,everyday"},
        {"name": "PS Append Content to File", "command": "Add-Content -Path log.txt -Value 'entry'", "shell": "powershell", "category": "PowerShell", "description": "Append text or content to the end of a specified file.", "example": "Add-Content log.txt 'done'", "tags": "powershell,append,everyday"},
        {"name": "PS Clear File Content", "command": "Clear-Content file.txt", "shell": "powershell", "category": "PowerShell", "description": "Delete all contents of a file while keeping the file itself.", "example": "Clear-Content temp.log", "tags": "powershell,truncate,everyday"},
        {"name": "PS Copy Item Recursive", "command": "Copy-Item -Path src -Destination dst -Recurse", "shell": "powershell", "category": "PowerShell", "description": "Copy files, folders, or registry keys recursively.", "example": "Copy-Item doc.txt backup\\", "tags": "powershell,copy,files,everyday"},
        {"name": "PS Move Item", "command": "Move-Item -Path src.txt -Destination dst.txt", "shell": "powershell", "category": "PowerShell", "description": "Move an item along with properties to another location.", "example": "Move-Item *.log logs\\", "tags": "powershell,move,files,everyday"},
        {"name": "PS Remove Item Recursive", "command": "Remove-Item -Path temp -Recurse -Force", "shell": "powershell", "category": "PowerShell", "description": "Delete files, folders, or registry keys permanently.", "example": "Remove-Item *.tmp", "tags": "powershell,rm,delete,specialized"},
        {"name": "PS Current Working Location", "command": "Get-Location", "shell": "powershell", "category": "PowerShell", "description": "Get current directory path object within PowerShell provider.", "example": "Get-Location", "tags": "powershell,pwd,path,everyday"},
        {"name": "PS Set Location Path", "command": "Set-Location C:\\lab", "shell": "powershell", "category": "PowerShell", "description": "Change working directory location to specified path.", "example": "Set-Location ~", "tags": "powershell,cd,path,everyday"},
        {"name": "PS Push Directory to Stack", "command": "Push-Location C:\\lab", "shell": "powershell", "category": "PowerShell", "description": "Push directory onto location stack and change location.", "example": "Push-Location logs", "tags": "powershell,pushd,everyday"},
        {"name": "PS Pop Directory from Stack", "command": "Pop-Location", "shell": "powershell", "category": "PowerShell", "description": "Change directory back to top location from stack.", "example": "Pop-Location", "tags": "powershell,popd,everyday"},
        {"name": "PS System Date and Time", "command": "Get-Date", "shell": "powershell", "category": "PowerShell", "description": "Get formatted current system date and time object.", "example": "Get-Date -Format 'yyyy-MM-dd'", "tags": "powershell,date,time,everyday"},
        {"name": "PS Command History List", "command": "Get-History", "shell": "powershell", "category": "PowerShell", "description": "Display list of commands entered in current PowerShell session.", "example": "Get-History -Count 10", "tags": "powershell,history,everyday"},
        {"name": "PS Find Available Cmdlets", "command": "Get-Command -Noun Process", "shell": "powershell", "category": "PowerShell", "description": "List all cmdlets, functions, and aliases matching pattern.", "example": "Get-Command *Network*", "tags": "powershell,cmdlet,search,everyday"},
        {"name": "PS Get Cmdlet Documentation", "command": "Get-Help Get-Process -Detailed", "shell": "powershell", "category": "PowerShell", "description": "Display help manual, parameters, and examples for cmdlet.", "example": "Get-Help Invoke-WebRequest -Online", "tags": "powershell,help,man,everyday"},
        {"name": "PS Inspect Object Members", "command": "Get-Member", "shell": "powershell", "category": "PowerShell", "description": "Inspect properties and methods available on piped object.", "example": "Get-Process | Get-Member", "tags": "powershell,member,inspect,everyday"},
        {"name": "PS Select Specific Properties", "command": "Select-Object Name, CPU, WorkingSet", "shell": "powershell", "category": "PowerShell", "description": "Select specific properties or unique items from dataset.", "example": "Get-Process | Select-Object -First 5", "tags": "powershell,select,filter,everyday"},
        {"name": "PS Filter Collection", "command": "Where-Object { $_.Handles -gt 500 }", "shell": "powershell", "category": "PowerShell", "description": "Filter collection of objects matching boolean condition.", "example": "Get-Service | Where-Object Status -eq 'Running'", "tags": "powershell,where,filter,everyday"},
        {"name": "PS ForEach Pipeline Iteration", "command": "ForEach-Object { $_.Name }", "shell": "powershell", "category": "PowerShell", "description": "Perform operation on each item in piped collection.", "example": "Get-ChildItem | ForEach-Object { $_.FullName }", "tags": "powershell,foreach,loop,everyday"},
        {"name": "PS Sort Collection by Property", "command": "Sort-Object -Property Length -Descending", "shell": "powershell", "category": "PowerShell", "description": "Sort piped objects ascending or descending by properties.", "example": "Get-ChildItem | Sort-Object Length -Descending", "tags": "powershell,sort,order,everyday"},
        {"name": "PS Group Objects by Key", "command": "Group-Object -Property Extension", "shell": "powershell", "category": "PowerShell", "description": "Group items sharing matching property values.", "example": "Get-ChildItem | Group-Object Extension", "tags": "powershell,group,aggregate,everyday"},
        {"name": "PS Measure Lines and Characters", "command": "Measure-Object -Line -Word -Character", "shell": "powershell", "category": "PowerShell", "description": "Count numeric properties, lines, words, or characters.", "example": "Get-Content app.log | Measure-Object -Line", "tags": "powershell,count,measure,everyday"},
        {"name": "PS Compare Two Collections", "command": "Compare-Object -ReferenceObject $a -DifferenceObject $b", "shell": "powershell", "category": "PowerShell", "description": "Compare two arrays or file contents showing differences.", "example": "Compare-Object (cat a.txt) (cat b.txt)", "tags": "powershell,diff,compare,everyday"},
        {"name": "PS Search Text in Files", "command": "Select-String -Path *.log -Pattern 'Exception'", "shell": "powershell", "category": "PowerShell", "description": "Search text strings and regular expression patterns in files.", "example": "Select-String -Path *.py -Pattern 'def test_'", "tags": "powershell,grep,search,everyday"},
        {"name": "PS Display GUI Grid View", "command": "Out-GridView", "shell": "powershell", "category": "PowerShell", "description": "Send output to an interactive GUI table with search/filter.", "example": "Get-Process | Out-GridView", "tags": "powershell,gui,table,everyday"},
        {"name": "PS Format Output as Auto Table", "command": "Format-Table -AutoSize", "shell": "powershell", "category": "PowerShell", "description": "Format output pipeline as column table with auto sizing.", "example": "Get-Process | Format-Table -AutoSize", "tags": "powershell,table,format,everyday"},
        {"name": "PS Export Pipeline to CSV", "command": "Export-Csv -Path export.csv -NoTypeInformation", "shell": "powershell", "category": "PowerShell", "description": "Export piped objects directly to CSV spreadsheet file.", "example": "Get-Process | Export-Csv procs.csv -NoTypeInformation", "tags": "powershell,csv,export,everyday"},
        {"name": "PS Import CSV into Objects", "command": "Import-Csv -Path export.csv", "shell": "powershell", "category": "PowerShell", "description": "Read CSV file into structured PowerShell objects.", "example": "Import-Csv procs.csv", "tags": "powershell,csv,import,everyday"},
        {"name": "PS Invoke Web Request", "command": "Invoke-WebRequest -Uri https://httpbin.org/get", "shell": "powershell", "category": "PowerShell", "description": "Send HTTP/HTTPS requests to websites or REST web services.", "example": "Invoke-WebRequest -Uri https://google.com", "tags": "powershell,curl,web,everyday"},
        {"name": "PS Invoke REST API JSON", "command": "Invoke-RestMethod -Uri https://api.github.com/zen", "shell": "powershell", "category": "PowerShell", "description": "Query REST API endpoint and automatically parse JSON response.", "example": "Invoke-RestMethod https://api.ipify.org?format=json", "tags": "powershell,rest,api,json,everyday"},
        {"name": "PS Run Background Job", "command": "Start-Job -ScriptBlock { Start-Sleep 10 }", "shell": "powershell", "category": "PowerShell", "description": "Run background asynchronous job in separate session.", "example": "Start-Job -ScriptBlock { Get-Process }", "tags": "powershell,job,async,specialized"},
        {"name": "PS Query Background Jobs", "command": "Get-Job", "shell": "powershell", "category": "PowerShell", "description": "List all background jobs and execution states in session.", "example": "Get-Job", "tags": "powershell,job,list,everyday"},
        {"name": "PS Receive Job Results", "command": "Receive-Job -Id 1 -Keep", "shell": "powershell", "category": "PowerShell", "description": "Retrieve completed output results from background job.", "example": "Receive-Job -Id 1", "tags": "powershell,job,results,everyday"},
        {"name": "PS Query Installed Hotfixes", "command": "Get-HotFix", "shell": "powershell", "category": "PowerShell", "description": "List Windows security hotfixes and updates installed on PC.", "example": "Get-HotFix | Sort-Object InstalledOn -Descending", "tags": "powershell,updates,hotfix,everyday"},
        {"name": "PS Query WMI OS Class", "command": "Get-WmiObject -Class Win32_OperatingSystem", "shell": "powershell", "category": "PowerShell", "description": "Query WMI system classes for OS and hardware details.", "example": "Get-WmiObject Win32_BIOS", "tags": "powershell,wmi,hardware,specialized"},
        {"name": "PS GUI Command Builder", "command": "Show-Command Get-Process", "shell": "powershell", "category": "PowerShell", "description": "Open GUI window to graphically build parameters for cmdlet.", "example": "Show-Command Get-Service", "tags": "powershell,gui,builder,everyday"},
    ]

    for item in curated_user_commands:
        cmd_key = item["command"].strip().lower()
        unified[cmd_key] = item

    # Output sorted list
    result_list = list(unified.values())
    result_list.sort(key=lambda x: (x.get("category", ""), x.get("name", "")))

    SEED_FILE.write_text(json.dumps(result_list, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[SUCCESS] Unified seed library written to {SEED_FILE}")
    print(f"Total commands in library: {len(result_list)}")

    # Summary by Category and Tier
    categories = {}
    everyday_count = 0
    specialized_count = 0
    for item in result_list:
        cat = item.get("category", "General")
        categories[cat] = categories.get(cat, 0) + 1
        tags = item.get("tags", "").lower()
        if "specialized" in tags:
            specialized_count += 1
        else:
            everyday_count += 1

    print("\nBreakdown by Category:")
    for cat, count in sorted(categories.items()):
        print(f"  - {cat:15}: {count:3} commands")
    print(f"\nTier classification:")
    print(f"  - Everyday:    {everyday_count} commands")
    print(f"  - Specialized: {specialized_count} commands")


if __name__ == "__main__":
    main()
