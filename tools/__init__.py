"""
Jarvis Tools Registry
=====================
Bundles and exports all executable tools for Gemini Function Calling.
Adding new skills is as simple as importing and registering their functions here.

NOTE: Delete tools (delete_file, delete_github_repository) and run_terminal_command
have been intentionally removed. Jarvis is not permitted to delete anything.
"""

from .github_tools import (
    create_github_repository,
    list_github_repositories,
    clone_github_repository,
)
from .memory_tools import (
    remember_user_fact,
    forget_user_fact
)
from .system_tools import (
    open_application,
    open_website,
    open_local_directory,
    move_file,
    copy_file,
    create_folder,
    gui_type_text,
    gui_press_key,
    gui_click_mouse,
    take_desktop_screenshot
)
from .file_tools import (
    read_workspace_file,
    write_workspace_file,
    patch_workspace_file
)
from .terminal_tools import (
    run_workspace_command
)
from .office_tools import (
    modify_excel_cell,
    read_excel_cell,
    modify_word_document
)
from .browser_tools import (
    browse_website,
    search_the_web,
    extract_page_data,
    take_browser_screenshot,
)
from .google_tools import (
    list_unread_emails,
    send_gmail_email,
    list_calendar_events,
    create_calendar_event,
    read_google_sheet,
    update_google_sheet,
    append_google_sheet,
    search_google_drive,
)
from .social_tools import (
    post_to_linkedin,
    post_to_twitter,
    post_to_instagram,
    post_to_facebook,
)



# List of function references passed to the Gemini API GenerateContentConfig
ALL_TOOLS = [
    create_github_repository,
    list_github_repositories,
    clone_github_repository,
    remember_user_fact,
    forget_user_fact,
    open_application,
    open_website,
    open_local_directory,
    move_file,
    copy_file,
    create_folder,
    gui_type_text,
    gui_press_key,
    gui_click_mouse,
    take_desktop_screenshot,
    read_workspace_file,
    write_workspace_file,
    patch_workspace_file,
    run_workspace_command,
    modify_excel_cell,
    read_excel_cell,
    modify_word_document,
    # Phase 2B — Browser tools
    browse_website,
    search_the_web,
    extract_page_data,
    take_browser_screenshot,
    # Phase 5 — Google Workspace tools
    list_unread_emails,
    send_gmail_email,
    list_calendar_events,
    create_calendar_event,
    read_google_sheet,
    update_google_sheet,
    append_google_sheet,
    search_google_drive,
    # Phase 6 — Social Media tools
    post_to_linkedin,
    post_to_twitter,
    post_to_instagram,
    post_to_facebook,
]



# Map to execute functions dynamically by name when returned from Gemini
TOOL_MAP = {
    func.__name__: func for func in ALL_TOOLS
}
