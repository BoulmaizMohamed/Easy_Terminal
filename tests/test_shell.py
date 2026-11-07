"""Unit tests for Command Center persistent shell sessions."""

import os
from command_center.shell import ShellSession


def test_powershell_echo():
    session = ShellSession("powershell")
    output_lines = []
    exit_code, cwd, duration = session.execute(
        "Write-Output 'Hello PowerShell'",
        on_output=output_lines.append,
    )
    session.close()

    assert exit_code == 0
    assert any("Hello PowerShell" in line for line in output_lines)
    assert cwd != ""
    assert duration >= 0


def test_powershell_cwd_persistence():
    session = ShellSession("powershell")
    initial_cwd = session.cwd
    exit_code, new_cwd, _ = session.execute("cd ..")
    session.close()

    assert exit_code == 0
    assert os.path.dirname(initial_cwd) == new_cwd


def test_powershell_exit_code_failure():
    session = ShellSession("powershell")
    output_lines = []
    exit_code, _, _ = session.execute(
        "Get-ChildItem NonExistentPathXYZ999",
        on_output=output_lines.append,
    )
    session.close()

    assert exit_code != 0
    assert len(output_lines) > 0


def test_interactive_command_rejection():
    session = ShellSession("powershell")
    output_lines = []
    exit_code, _, _ = session.execute("vim test.txt", on_output=output_lines.append)
    session.close()

    assert exit_code == 1
    assert any("interactive full-screen program" in line.lower() for line in output_lines)
