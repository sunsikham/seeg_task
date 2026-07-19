# Agent Instructions

## Execution Policy

- Do not create, modify, delete, move, or rename files unless the user explicitly requests that action.
- Treat phrases such as “I’m thinking of creating this,” “it would be nice to have,” “I want to make this,” or “what is this?” as discussion, not authorization to act.
- Before creating or modifying a file, discuss its purpose, contents, and structure with the user.
- A draft may be presented in chat, but it must not be written to the filesystem until the user explicitly approves implementation.
- Act only after a clear instruction such as “create it,” “apply it,” “modify it,” “implement it,” or “proceed.”
- Do not perform adjacent work, including Git initialization, commits, configuration changes, dependency installation, or additional file creation, unless the user explicitly requests it.
- When an instruction could reasonably mean either discussion or implementation, treat it as discussion and ask before changing the workspace.
- Implement only the scope that was discussed and approved. Do not add unrequested improvements or supporting files.
- Do not delete, revert, or overwrite existing files, data, or settings without explicit user authorization.
