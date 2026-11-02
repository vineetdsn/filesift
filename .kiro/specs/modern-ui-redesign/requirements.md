# Requirements Document

## Introduction

FileSift is a local Windows desktop app (Python 3.12, PySide6 6.8.1) that scans folders, finds exact and similar duplicate files, classifies old screenshots, junk and important files, and moves files to the Recycle Bin or an Important folder after confirmation.

This feature makes two changes:

1. **Remove Bills & Warranty.** The bill/warranty vault was never meant to be part of FileSift. The Bills tab, the bill and reminder modules, the tray reminder timer, the `--reminders` command-line mode and the related tests are removed. The "vault" folder setting is kept only as the location of the Important folder.
2. **Modern UI redesign.** The old tabbed, table-based UI is replaced with a modern look based on the user's reference image: a dark navy-slate shell, frosted/translucent panels, large rounded cards with soft shadows, a glowing blue/cyan accent, light lavender gradient content cards, list rows with a circular icon, title, subtitle and pill-shaped action button, large light-weight numeric stats, and thin line icons.

All existing duplicate detection, cleanup classification, OCR/PDF text reading, protected-folder and Recycle Bin safety behaviour stays the same. The app has to stay responsive with scans of tens of thousands of files.

## Glossary

- **FileSift**: The desktop application as a whole.
- **Main_Window**: The top-level FileSift window that holds the Sidebar and the active Page.
- **Sidebar**: The vertical navigation panel on the left edge of the Main_Window, containing one icon button per Page.
- **Page**: One full content view shown next to the Sidebar. The Pages are Scan_Page, Duplicates_Page and Cleanup_Page. There is no other Page.
- **Scan_Page**: The Page where the user picks scan folders, Protected_Folders, scan options and the Important_Folder location, starts or cancels a scan, and sees Stat_Cards.
- **Duplicates_Page**: The Page that shows Duplicate_Groups as Group_Cards and lets the user mark copies for deletion.
- **Cleanup_Page**: The Page that lists scanned files as List_Rows with filters by verdict and category, and lets the user trash or move ticked files.
- **Count_Badge**: A small numeric badge drawn on a Sidebar button.
- **Theme_Toggle**: The two-state control in the Sidebar that switches between Dark_Theme and Light_Theme (only present where the Light_Theme is provided).
- **Scan_Result**: The output of one completed scan: the list of scanned files and the list of Duplicate_Groups.
- **Stage_Label**: The text on the Scan_Page that shows the current scan stage, progress counts, or the outcome of the last scan.
- **Duplicate_Group**: A set of two or more files that the existing duplicate detector considers exact or similar copies of each other.
- **Reclaimable_Size**: For one Duplicate_Group, the sum of the sizes of all files in the group except the single largest file (the existing `DupGroup.wasted` value).
- **Keeper**: The file in a Duplicate_Group that the selected Keeper_Rule picks to keep.
- **Keeper_Rule**: One of the existing rules in `KEEPER_RULES` used by auto-select to choose the Keeper.
- **Verdict**: The cleanup classification of a file: "Safe to delete", "Review" or "Keep".
- **Category**: The cleanup category the existing classifier assigns to a file (for example screenshot, photo, document).
- **Score**: The numeric cleanup score the existing classifier assigns to a file; a higher Score means a stronger case for deletion.
- **File_Date**: The date shown for a file: the date taken if known, otherwise the earlier of the file's modification and creation dates.
- **Important_Tag**: A tag the classifier assigns to a file whose text matches important-document keywords (for example "Receipts-Bills", "Warranty", IDs).
- **Protected_File**: A file located under a Protected_Folder or under the Important_Folder. Protected_Files are scanned but are never offered for deletion or moving.
- **Protected_Folder**: A folder the user lists as protected on the Scan_Page.
- **Important_Folder**: The folder into which "Move to Important folder" places files, in per-tag or per-category subfolders. The Important_Folder location is stored in the existing `vault_dir` setting.
- **Legacy_Bill_Data**: Bill records in the `bills` table, reminder log entries in the `reminders_sent` table, and bill files copied into the vault folder by FileSift 1.0.0. FileSift keeps this data on disk but no longer reads or shows it.
- **Recycle_Bin_Operation**: Sending one or more confirmed files to the Windows Recycle Bin through Send2Trash.
- **Move_Operation**: Moving one or more confirmed files into the Important_Folder.
- **Theme**: The set of colours, radii, spacing, shadows, fonts and widget styles applied to the whole FileSift UI.
- **Theme_Module**: The single central module that defines every Theme colour, radius, spacing value and font size.
- **Dark_Theme**: The primary Theme: navy-slate background, translucent panels, light lavender gradient content cards and blue/cyan accent.
- **Light_Theme**: An optional secondary Theme with light backgrounds and the same blue/cyan accent.
- **Accent_Color**: The blue/cyan highlight colour used for primary actions, selection, focus and progress.
- **Stat_Card**: A rounded card that shows one large light-weight number with a short label underneath.
- **Group_Card**: A rounded card on the Duplicates_Page that represents one Duplicate_Group and shows its files as a grid of Thumbnail_Tiles.
- **Thumbnail_Tile**: A tile inside a Group_Card showing one file's thumbnail (or a file-type placeholder), file name, size, resolution and a selection toggle.
- **List_Row**: A row on the Cleanup_Page or Scan_Page containing a circular icon on the left, a title and a subtitle in the middle, and a Pill_Button, toggle or slider on the right.
- **Pill_Button**: A fully rounded (capsule-shaped) button or toggle.
- **Preview_Panel**: The side panel that shows a larger preview and details of the currently selected file.
- **Thumbnail_Loader**: The component that decodes and scales image thumbnails off the GUI thread and caches the results in memory.
- **Confirm_Dialog**: The themed modal dialog used to confirm Recycle_Bin_Operations and Move_Operations.
- **Message_Dialog**: The themed modal dialog with a title, a message and one primary Pill_Button, used for informational, warning and error messages outside the Confirm_Dialog.
- **Status_Area**: The text area on each Page that shows the result of the last completed action on that Page.
- **Store**: The SQLite storage module (`store.py`) holding the feature cache and settings.
- **Test_Suite**: The automated tests in `tests/test_core.py` and `tests/test_ui_smoke.py`.

## Requirements

### Requirement 1: Remove the Bills & Warranty user interface

**User Story:** As a FileSift user, I want the Bills & Warranty feature gone from the app, so that FileSift only contains the file cleanup features I asked for.

#### Acceptance Criteria

1. THE Main_Window SHALL provide navigation to exactly three Pages, in this order: Scan_Page, Duplicates_Page and Cleanup_Page, and SHALL show no fourth Page and no Page, tab or menu entry named "Bills & Warranty".
2. THE Cleanup_Page SHALL offer exactly two file actions on ticked files: one "Move to Recycle Bin" control that moves the ticked files to the Recycle Bin and one "Move to Important folder" control that moves the ticked files to the Important_Folder, where a file action is any control that moves, deletes or records a file (filter selectors, the sort selector, "Tick all safe to delete" and "Clear ticks" are not file actions), and THE Cleanup_Page SHALL show no control for adding a selected file as a bill.
3. WHEN FileSift starts, THE Main_Window SHALL start without creating any reminder timer or running any reminder check, so that no warranty reminder notification appears at any time during the session, including when the Legacy_Bill_Data holds bill records whose reminder dates are due.
4. WHILE FileSift is running, THE Main_Window SHALL show no FileSift icon in the Windows notification area (system tray) and SHALL show no tray notifications, because no remaining FileSift feature uses the system tray.
5. THE Main_Window SHALL contain no Page, control, dialog or notification for adding, viewing, editing, deleting or exporting bill records or warranty reminders; the Important_Tag categories "Receipts-Bills" and "Warranty" shown on the Cleanup_Page belong to cleanup tagging, are outside this removal, and SHALL remain unchanged.
6. IF the FileSift data store contains Legacy_Bill_Data saved by an earlier FileSift version, THEN THE Main_Window SHALL start without an error dialog or crash, SHALL display none of the Legacy_Bill_Data, and SHALL leave the Legacy_Bill_Data and any files in the vault folder unchanged on disk.
7. WHEN the user closes the Main_Window, THE Main_Window SHALL end the FileSift process within 5 seconds, leaving no FileSift process running in the background.

### Requirement 2: Remove bill and reminder code and the command-line reminder mode

**User Story:** As the maintainer, I want the bill, reminder and scheduler code removed from the codebase, so that there is no dead code to maintain.

#### Acceptance Criteria

1. THE FileSift codebase SHALL contain no `ui_bills.py`, `bills.py` or `reminders.py` modules in the `filesift` package directory or anywhere else in the repository.
2. THE FileSift codebase SHALL contain no imports of, or references to, the removed bill and reminder modules, and no code that exists only to support them, across the Python files in the `filesift` package, `run.py` and the `tests` directory; code that exists only to support them includes the bills tab, the startup and hourly reminder checks, the tray reminder notification function, the "Add selected as bill..." button and its signal in the cleanup tab, the `--reminders` branch in the entry point, the bill and reminder tests, and the creation of bill and reminder-log tables in a new database, and a case-insensitive search of those files for "bill", "reminder", "warranty" and "Task Scheduler" SHALL match only the Important_Tag keyword groups in the classifier, the tests that cover those keyword groups, and the tests that verify Requirement 3.2.
3. WHEN FileSift is launched with the `--reminders` argument, THE FileSift SHALL open the Main_Window in the same way as a launch without arguments, SHALL show no reminder notification, and SHALL keep running until the user closes the Main_Window instead of exiting on its own after a delay.
4. THE `run.py` docstring, the package docstring in `filesift/__init__.py`, the module docstrings of `filesift/app.py` and `filesift/store.py`, and the comments in `requirements.txt` SHALL describe FileSift without mentioning bills, warranty reminders, the `--reminders` argument or Task Scheduler.
5. THE classifier SHALL keep the existing Important_Tag keyword groups unchanged, including "Receipts-Bills" and "Warranty", because Important_Tags are part of the cleanup feature; for example, a file whose extracted text contains "tax invoice" SHALL still receive the "Receipts-Bills" Important_Tag, and a file whose extracted text contains "serial number" SHALL still receive the "Warranty" Important_Tag.
6. WHEN the Test_Suite is run after the removal, THE Test_Suite SHALL complete with zero failures and zero import errors, and the duplicate-finding, classification and UI smoke tests SHALL still run.
7. IF FileSift starts with an existing database file from an earlier version that contains Legacy_Bill_Data, THEN THE FileSift SHALL open the Main_Window without raising an error, SHALL keep the stored settings and cached scan data usable, and SHALL keep the database file in place.
8. WHILE the Main_Window is open, THE FileSift SHALL show no warranty, return-window or other bill reminder tray notifications, including during the first 5 seconds after launch.

### Requirement 3: Keep existing user data safe after the removal

**User Story:** As an existing FileSift user, I want my existing database to keep working after the upgrade, so that my cache and settings are preserved and nothing is lost.

#### Acceptance Criteria

1. WHEN the Store opens a database file that does not contain a `cache` table, a `settings` table, or both, THE Store SHALL create each missing table and SHALL NOT create a `bills` table or a `reminders_sent` table.
2. WHEN the Store opens a database that already contains a `bills` table, a `reminders_sent` table, or both, THE Store SHALL keep those tables with the same table names, column definitions, row count and row values as before the open, on every open and after any writes to the `cache` and `settings` tables while the database is open.
3. WHEN the Store opens a database created by FileSift 1.0.0, THE Store SHALL, without raising an error, return each existing `cache` row whose stored size and modification time match the queried file, return `scan_roots` and `protected_dirs` as the same folder-path lists in the same order as stored, and return `vault_dir` as the same path as stored.
4. WHEN the Store opens a database file that already contains the `cache` and `settings` tables, THE Store SHALL keep the column definitions, row count and row values of both tables unchanged by the open operation.
5. IF a FileSift 1.0.0 database has no `scan_roots`, `protected_dirs` or `vault_dir` setting, or stores a `scan_roots` or `protected_dirs` value that is not a valid list, THEN THE Store SHALL return an empty list for that list setting, return the default Important_Folder location defined in Requirement 4.3 for a missing `vault_dir`, raise no error, and leave the stored setting value unchanged.
6. IF the database file cannot be opened or read because the file is corrupt, locked by another process, or not a SQLite database, THEN THE Store SHALL raise an error indicating the database could not be opened, and SHALL NOT delete, overwrite or recreate the existing database file.

### Requirement 4: Important folder location

**User Story:** As a FileSift user, I want to choose where important files are moved, so that I control the location of my Important folder.

#### Acceptance Criteria

1. THE Scan_Page SHALL show the full absolute path of the current Important_Folder next to the label "Important folder".
2. WHEN the user picks a folder in the folder picker opened by the "Change..." action next to the Important_Folder location, THE Scan_Page SHALL save the chosen absolute path to the `vault_dir` setting, display the new path in place of the previous one when the picker closes back to the Scan_Page, and keep showing that path after FileSift is restarted.
3. WHILE no `vault_dir` setting exists, THE FileSift SHALL use `<user home folder>\Documents\FileSift Vault` as the Important_Folder location, both for display on the Scan_Page and as the destination for "Move to Important folder".
4. WHEN a scan starts, THE Scan_Page SHALL treat the Important_Folder and all of its subfolders as a Protected_Folder in addition to the user's Protected_Folders, so that no file inside the Important_Folder is offered for deletion or move in the Scan_Result.
5. WHEN the user confirms "Move to Important folder" on one or more ticked files, THE Cleanup_Page SHALL move each ticked non-protected file directly into `Important_Folder\<first Important_Tag>` if the file has at least one Important_Tag, or directly into `Important_Folder\<Category>` (Category name with its first letter capitalized) if the file has none, with no additional intermediate subfolder, create any destination subfolder that does not exist, remove each moved file from the Cleanup_Page list, and show the number of files moved in the Status_Area.
6. IF a file with the same name already exists in the destination subfolder, THEN THE Cleanup_Page SHALL move the file under the name `<name> (N)<extension>`, where N is the lowest integer starting at 2 that does not match an existing file, and SHALL NOT overwrite or modify the existing file.
7. IF moving a file fails (for example, the file is locked, missing, or the destination is not writable), THEN THE Cleanup_Page SHALL leave that file at its original location and in the Cleanup_Page list, continue moving the remaining ticked files, and after the operation show the failed files and reasons in the error Message_Dialog defined in Requirement 13.4.
8. IF the user closes the folder picker opened by the "Change..." action without choosing a folder, THEN THE Scan_Page SHALL leave the `vault_dir` setting and the displayed Important_Folder path unchanged.

### Requirement 5: Application shell and navigation

**User Story:** As a FileSift user, I want a modern sidebar layout instead of old-style tabs, so that the app feels current and is easy to move around.

#### Acceptance Criteria

1. THE Main_Window SHALL show the Sidebar across the full height of the Main_Window's left edge and the active Page in the area to the right of the Sidebar, with no tab bar shown.
2. THE Sidebar SHALL show exactly one icon button per Page, ordered top to bottom as Scan_Page, Duplicates_Page, Cleanup_Page, with no other Page button, and each button SHALL have a single-colour outline icon drawn with lines 2 pixels wide or thinner, plus either a visible text label naming the Page or a tooltip naming the Page that appears within 1 second of the pointer resting on the button.
3. WHEN the user clicks a Sidebar button, THE Main_Window SHALL show the matching Page within 500 milliseconds and highlight that Sidebar button with the Accent_Color, and if the clicked button's Page is already active, the shown Page and highlight SHALL stay the same.
4. WHEN a scan completes with one or more Duplicate_Groups, THE Main_Window SHALL show the Duplicates_Page, whichever Page was active when the scan completed.
5. WHEN a scan completes with zero Duplicate_Groups, THE Main_Window SHALL show the Cleanup_Page, whichever Page was active when the scan completed.
6. WHILE at least one scan has completed in the current session, THE Sidebar SHALL show a Count_Badge on the Duplicates_Page button equal to the number of Duplicate_Groups and a Count_Badge on the Cleanup_Page button equal to the number of files whose Verdict is "Safe to delete", hide any Count_Badge whose count is 0, show counts above 999 as "999+", and update a Count_Badge within 1 second after its count changes; before the first scan of the session completes, the Sidebar SHALL show no Count_Badge.
7. THE Main_Window SHALL open at 1250 x 800 pixels and SHALL limit user resizing to a minimum of 1000 x 650 pixels, and at 1000 x 650 pixels every Sidebar button SHALL be fully visible and every control on the active Page SHALL be either fully visible or reachable by scrolling, with no controls overlapping.
8. WHEN the Main_Window opens, THE Main_Window SHALL show the Scan_Page and highlight the Scan_Page Sidebar button with the Accent_Color.
9. THE Sidebar SHALL highlight exactly one button with the Accent_Color at all times, namely the button matching the active Page, including after Page changes the user did not start by clicking a Sidebar button, such as scan completion.
10. IF a scan is cancelled or fails, THEN THE Main_Window SHALL keep the currently active Page shown and SHALL leave both Count_Badges at the values they had before that scan started.

### Requirement 6: Visual theme

**User Story:** As a FileSift user, I want a polished dark glass-style look like my reference image, so that the app looks modern and pleasant to use.

#### Acceptance Criteria

1. WHEN FileSift starts, THE FileSift SHALL apply the Dark_Theme to the Main_Window, every Page, and every Qt-drawn dialog and message box before the Main_Window is first shown, so that no window, Page or dialog opened during the session displays the default Fusion colours; native Windows file pickers are excluded.
2. THE Dark_Theme SHALL use a navy-slate main background in the range of `#262A40` to `#2F3450`, draw panel surfaces as translucent (frosted) fills with an opacity between 60% and 90%, fill content cards with a vertical gradient from a light lavender (hue 240° to 280°, HSL lightness at least 85%) at the top to white at the bottom, and use an Accent_Color with a hue between 190° and 230° (blue/cyan).
3. THE Theme SHALL draw cards and panels with a corner radius of at least 20 pixels, buttons and inputs (line edits, combo boxes) with a corner radius of at least 10 pixels, and Pill_Buttons with a corner radius equal to half the button height so that both ends are fully rounded.
4. THE Theme SHALL draw a drop shadow under every card with a blur radius of at least 16 pixels, a vertical offset of 0 to 8 pixels and an opacity of no more than 40%, and SHALL draw an Accent_Color glow with a blur radius of at least 12 pixels around the primary action button on each Page and around any button that has keyboard focus.
5. THE Theme SHALL provide styled versions of buttons, Pill_Buttons, checkboxes, toggles, combo boxes, sliders, progress bars, scrollbars, list views, tooltips, line edits and menus, where every styled control takes its colours from the Theme palette and its corner radius from the values in criterion 3, and progress bar fills, slider handles, checked checkboxes, checked toggles and selected list items use the Accent_Color.
6. THE Theme SHALL keep text contrast against the background directly behind the text, measured with WCAG 2.1 contrast rules, at a ratio of at least 4.5:1 for body text (below 18 pt regular or 14 pt bold) and at least 3:1 for large text and for the borders of input controls, on the navy-slate background, on translucent panels, on lavender gradient cards (measured against the lightest point of the gradient) and on Accent_Color buttons; text on disabled controls is excluded.
7. THE Theme_Module SHALL define all colours, radii, spacing and font sizes, and no Page, dialog or widget module SHALL contain a literal colour value, corner radius or font size outside the Theme_Module.
8. THE Theme SHALL give buttons, Pill_Buttons, checkboxes, toggles, combo boxes, line edits, list view items and menu items a hover state, a pressed state, a keyboard-focus state and a disabled state, where each state differs visibly from the default state in at least one of fill colour, border colour or glow, and disabled controls render at an opacity between 40% and 60% of their enabled appearance with no hover or pressed changes.

### Requirement 7: Typography and icons

**User Story:** As a FileSift user, I want clean modern fonts and icons, so that text and controls look crisp and consistent.

#### Acceptance Criteria

1. WHEN FileSift starts, THE FileSift SHALL set the application font family to the first family in the ordered list "Segoe UI Variable Text", "Segoe UI" that is installed on the system, before the Main_Window is first shown, and SHALL keep the system default point size.
2. IF none of the font families in the ordered list are installed, THEN THE FileSift SHALL use the Qt default system font and finish starting without showing an error dialog and without exiting.
3. THE Theme SHALL render Stat_Card numbers in the application font family, at a font weight of 300 or lighter and a size of at least 32 points.
4. THE FileSift SHALL draw all Sidebar, List_Row and button icons as outline icons with a stroke width between 1 and 2 device-independent pixels and no filled shapes, at a size between 16 and 24 device-independent pixels, in the Theme colour defined for the text of the control that holds the icon, and in the Theme disabled colour while that control is disabled.
5. THE FileSift SHALL ship its icons inside the FileSift package or generate them in code, so that every icon appears with no network access and with no packages installed beyond those in `requirements.txt`.
6. WHILE the Windows display scaling is between 100% and 200%, THE FileSift SHALL render each icon at the screen's device pixel ratio, so that no icon is shown as a lower-resolution image scaled up.
7. IF an icon cannot be loaded or generated, THEN THE FileSift SHALL show the control without that icon, keep the control's text label visible and clickable, and continue running.

### Requirement 8: Scan page

**User Story:** As a FileSift user, I want a clean scan screen with clear stats, so that I can set up a scan and see the results summary at a glance.

#### Acceptance Criteria

1. THE Scan_Page SHALL show the scan folders and the Protected_Folders as two separate rounded cards, each listing its folder paths and offering an "Add folder" action and a "Remove" action.
2. WHEN the user picks a folder through "Add folder", THE Scan_Page SHALL append the folder's path to that card's list if the path is not already in that list, and SHALL leave the list unchanged if the path is already in that list.
3. WHEN the user activates "Remove", THE Scan_Page SHALL remove every selected folder from that card's list, and SHALL leave the list unchanged if no folder is selected.
4. THE Scan_Page SHALL show the scan options as List_Rows, each with a control on the right: similar-image detection, with a toggle that is on by default; the strict/loose distance, with a slider that covers whole numbers from 2 (strict) to 12 (loose), has a default value of 6, and shows its current value with a "recommended" mark when the value is 6; and OCR/PDF text reading, with a toggle.
5. THE Scan_Page SHALL show in the OCR/PDF text reading List_Row's subtitle whether Tesseract OCR is installed and whether PyMuPDF is installed.
6. IF Tesseract OCR and PyMuPDF are both unavailable, THEN THE Scan_Page SHALL turn the OCR/PDF text reading toggle off and disable the toggle.
7. THE Scan_Page SHALL show five Stat_Cards: files scanned, total size scanned, Duplicate_Groups found, space reclaimable from duplicates (the sum of the Reclaimable_Size of every Duplicate_Group), and files with Verdict "Safe to delete", with counts shown as whole numbers and sizes shown in human-readable units (B, KB, MB, GB or TB).
8. WHILE no scan has completed in the current session, THE Scan_Page SHALL show "—" as the value of every Stat_Card.
9. WHEN a scan completes, THE Scan_Page SHALL update all five Stat_Cards with the values from the Scan_Result and show a completion summary in the Stage_Label.
10. WHILE a scan is running, THE Scan_Page SHALL show an Accent_Color progress bar, the current stage name with done/total counts in the Stage_Label, an enabled "Cancel" button and a disabled "Start scan" button, and while the current stage reports a total of 0, the progress bar SHALL show an indeterminate (busy) state and the Stage_Label SHALL omit the counts.
11. WHILE no scan is running, THE Scan_Page SHALL enable the "Start scan" button, disable the "Cancel" button, and show the progress bar empty.
12. IF a scan is cancelled by the user or ends with an error, THEN THE Scan_Page SHALL return to the not-running state described in criterion 11, show in the Stage_Label that the scan was cancelled or show the error description, and leave every Stat_Card with the value it had before the scan started.
13. IF the user starts a scan with no scan folders listed, THEN THE Scan_Page SHALL show a Message_Dialog asking the user to add at least one folder, SHALL not start the scan, and SHALL leave the `scan_roots` and `protected_dirs` settings unchanged.
14. WHEN a scan starts, THE Scan_Page SHALL save the scan folders to the `scan_roots` setting and the Protected_Folders to the `protected_dirs` setting before the background scan begins, keeping each list's displayed order.

### Requirement 9: Duplicates page

**User Story:** As a FileSift user, I want to see duplicate copies side by side as thumbnails, so that I can quickly decide which copies to delete.

#### Acceptance Criteria

1. WHEN a Scan_Result is loaded, THE Duplicates_Page SHALL show one Group_Card per Duplicate_Group, ordered by Reclaimable_Size from largest to smallest, with a header containing the 1-based group number, the group kind ("exact" or "similar"), the file count and the Reclaimable_Size.
2. THE Group_Card SHALL show every file of the Duplicate_Group as a Thumbnail_Tile containing a thumbnail (for images that can be decoded) or a file-type placeholder (for non-image files and images that cannot be decoded), the file name, the human-readable file size, the resolution in "width x height" pixels (for images only), the File_Date and the containing folder path (in a tooltip or subtitle).
3. THE Duplicates_Page SHALL show a summary line with the number of Duplicate_Groups and the total reclaimable size, equal to the sum of the Reclaimable_Size of all displayed Group_Cards, and SHALL update the summary line each time Group_Cards are added or removed.
4. WHEN the user clicks a Thumbnail_Tile outside the tile's selection control, THE Duplicates_Page SHALL show that file in the Preview_Panel without changing the file's marked state.
5. WHEN the user toggles a non-protected Thumbnail_Tile's selection control, THE Duplicates_Page SHALL switch that file between marked and unmarked for deletion, show an Accent_Color outline or overlay on the tile while the file is marked, and remove the outline or overlay when the file is unmarked.
6. IF the user tries to mark a file that would leave every file in its Duplicate_Group marked, THEN THE Duplicates_Page SHALL keep that file unmarked and show the message "Cannot select every copy in a group: at least one must be kept.", where Protected_Files count as unmarked, so a Duplicate_Group containing a Protected_File allows every non-protected file to be marked.
7. THE Duplicates_Page SHALL show each Protected_File's Thumbnail_Tile with a "Protected" badge and without a selection control, so that no user action and no Auto-select can mark a Protected_File.
8. WHEN the user runs "Auto-select" with a chosen Keeper_Rule, THE Duplicates_Page SHALL, in each Duplicate_Group, pick exactly one Keeper (chosen from the group's Protected_Files if the group contains any, otherwise from all files in the group, using the Keeper_Rule with its fixed tie-break order), unmark the Keeper, mark every other non-protected file, replace any marks made before the run, and show a "Keep" badge on each Keeper's Thumbnail_Tile.
9. WHEN the user runs "Clear selection", THE Duplicates_Page SHALL unmark every file in every Group_Card and remove every "Keep" badge.
10. THE Duplicates_Page SHALL show the number of marked files and their total human-readable size next to the "Move to Recycle Bin" button, and SHALL update both values within 200 ms after each mark, unmark, Auto-select, Clear selection or Recycle_Bin_Operation.
11. WHEN the user confirms "Move to Recycle Bin" in the Confirm_Dialog described in Requirement 13.3, THE Duplicates_Page SHALL send every marked file to the Recycle Bin, remove each successfully moved file from the cache, remove the matching Thumbnail_Tiles, and remove each Group_Card left with fewer than two files.
12. WHEN one or more files are moved to the Recycle Bin, THE Duplicates_Page SHALL show in the Status_Area the number of files moved and the space freed, where space freed is the sum of the sizes of the successfully moved files only.
13. IF one or more files fail to move to the Recycle Bin, THEN THE Duplicates_Page SHALL keep each failed file's Thumbnail_Tile in its Group_Card with its marked state preserved, still remove the files that moved successfully, and show the failed files, each named with its reason, in the error Message_Dialog defined in Requirement 13.4.
14. FOR ALL Duplicate_Groups and all sequences of mark, unmark, Auto-select and Clear selection actions, THE Duplicates_Page SHALL keep at least one file (protected or unmarked) not marked in each Duplicate_Group (invariant).
15. FOR ALL Duplicate_Groups, THE set of files marked by Auto-select SHALL contain no Protected_File and no Keeper (invariant).
16. IF the user cancels the "Move to Recycle Bin" Confirm_Dialog, THEN THE Duplicates_Page SHALL move no files and SHALL keep every Group_Card, Thumbnail_Tile and marked state unchanged.
17. IF the user activates "Move to Recycle Bin" while no file is marked, THEN THE Duplicates_Page SHALL show a Message_Dialog indicating that nothing is selected and SHALL not open the Confirm_Dialog.
18. IF a loaded Scan_Result contains no Duplicate_Groups, or the last Group_Card is removed, THEN THE Duplicates_Page SHALL show an empty-state message indicating that no duplicates were found and a summary line with 0 groups and 0 B reclaimable.

### Requirement 10: Cleanup page

**User Story:** As a FileSift user, I want old screenshots, junk and important files shown as clean list rows with filters, so that I can review and act on them easily.

#### Acceptance Criteria

1. WHEN a Scan_Result is loaded, THE Cleanup_Page SHALL show a summary with the total number of files scanned, the count of files for each Verdict ("Safe to delete", "Review", "Keep"), the combined size of files with Verdict "Safe to delete" in human-readable units (B, KB, MB or GB), the count of files with at least one Important_Tag, and a statement that no file is deleted until the user confirms.
2. THE Cleanup_Page SHALL offer verdict filters "All", "Safe to delete", "Review", "Keep" and "Important" as a row of Pill_Buttons with "All" selected by default, and a category filter listing "All categories" (selected by default) followed by every distinct Category in the Scan_Result in alphabetical order, where the "Important" filter matches every file with at least one Important_Tag regardless of its Verdict.
3. WHEN the user changes the verdict filter or the category filter, THE Cleanup_Page SHALL list only the files that match both the selected verdict filter and the selected category filter, show the number of matching files, and untick every listed file.
4. THE Cleanup_Page SHALL show each listed file as a List_Row with a circular icon or thumbnail on the left, the file name as the title, a subtitle containing the Category, the reasons (replaced by the Important_Tags when the file has at least one Important_Tag), the age in whole days since the File_Date and the size in human-readable units, and on the right a Verdict pill and a tick toggle, where a Protected_File's List_Row shows a "Protected" indicator in place of the tick toggle.
5. THE Cleanup_Page SHALL sort listed files by Score descending and then by File_Date ascending (oldest first) by default, and SHALL let the user switch the sort to age descending (oldest first) or size descending (largest first).
6. WHEN the user selects a List_Row, THE Cleanup_Page SHALL show that file in the Preview_Panel.
7. WHEN the user runs "Tick all safe to delete", THE Cleanup_Page SHALL tick every listed non-protected file whose Verdict is "Safe to delete" and leave the tick state of all other listed files unchanged.
8. WHEN the user runs "Clear ticks", THE Cleanup_Page SHALL untick every listed file.
9. WHEN the user confirms "Move to Recycle Bin" in the Confirm_Dialog described in Requirement 13.3, THE Cleanup_Page SHALL send every ticked non-protected file to the Recycle Bin, remove each successfully recycled file from the list, the summary counts and the cache, and show in the Status_Area the number of files moved.
10. IF one or more ticked non-protected files have Verdict "Keep" or at least one Important_Tag, THEN THE Confirm_Dialog for "Move to Recycle Bin" SHALL show the warning described in Requirement 13.6, stating the number of such files.
11. WHEN the user confirms "Move to Important folder" in the Confirm_Dialog described in Requirement 13.7, THE Cleanup_Page SHALL move every ticked non-protected file as described in Requirement 4.5, remove each successfully moved file from the list, the summary counts and the cache, and show in the Status_Area the number of files moved.
12. IF a Recycle_Bin_Operation or Move_Operation fails for one or more files, THEN THE Cleanup_Page SHALL keep each failed file listed with the file left at its original location, still remove the files that succeeded, and show each failed file path with its failure message in the error Message_Dialog defined in Requirement 13.4.
13. IF no non-protected file is ticked when the user runs "Move to Recycle Bin" or "Move to Important folder", THEN THE Cleanup_Page SHALL show the message "Nothing ticked." in a Message_Dialog, perform no file operation and show no Confirm_Dialog.
14. IF the user cancels the Confirm_Dialog for "Move to Recycle Bin" or "Move to Important folder", THEN THE Cleanup_Page SHALL perform no file operation and keep the list, the tick states and the summary unchanged.
15. IF no Scan_Result has been loaded, THEN THE Cleanup_Page SHALL show a message prompting the user to run a scan first and list no files.
16. IF more than 20,000 files match the selected filters, THEN THE Cleanup_Page SHALL list only the first 20,000 files in the current sort order and show the total number of matching files followed by "(showing first 20000)", as defined in Requirement 12.9.

### Requirement 11: Preview panel

**User Story:** As a FileSift user, I want a large preview of the selected file, so that I can check a file before deleting it.

#### Acceptance Criteria

1. WHEN a file whose extension is in the supported image set (.jpg, .jpeg, .png, .webp, .bmp, .gif, .tif, .tiff, .heic, .heif) is selected on the Duplicates_Page or Cleanup_Page, THE Preview_Panel SHALL display the image inside a rounded card, scaled to fit entirely within the card with its aspect ratio preserved, never enlarged beyond its original pixel dimensions, and rotated or mirrored according to the image's EXIF orientation tag (no transformation applied when the tag is absent).
2. IF the selected file's extension is not in the supported image set, or the image data cannot be decoded, THEN THE Preview_Panel SHALL show, in place of the image, a file-type placeholder containing the file's extension (or a generic "file" label when the file has no extension), and SHALL still show the file details defined in criterion 5.
3. WHILE no file is selected on the Duplicates_Page or Cleanup_Page, including after the previously selected file is removed from the list, THE Preview_Panel SHALL show the text "Select a file to preview" and SHALL show no image, placeholder or file details.
4. THE Preview_Panel SHALL let the user select the full file path text with the mouse and copy the selection with Ctrl+C or the right-click context menu, with the clipboard then containing exactly the selected characters of the absolute path, and SHALL wrap paths longer than the panel width onto additional lines without truncating them.
5. WHEN a file is selected on the Duplicates_Page or Cleanup_Page, THE Preview_Panel SHALL show below the preview card, in this order: the full absolute path, the resolution as width × height in pixels (omitted when unknown), the file size in human-readable units (B, KB, MB, GB), the File_Date, the Category, the Important_Tags (omitted when the file has none) and the reasons (omitted when the file has none).
6. WHEN the selection changes from one file to another, THE Preview_Panel SHALL replace the previous preview and details with those of the newly selected file within 1 second for image files up to 50 MB, and SHALL show the image and the details of the same file at all times.
7. IF the selected file no longer exists at its recorded path or cannot be read when the file is selected, THEN THE Preview_Panel SHALL show the file-type placeholder together with an indication that the file is missing or unreadable, SHALL still show the recorded file details, and SHALL leave the file's entry in the list unchanged.

### Requirement 12: Responsiveness with large scans

**User Story:** As a FileSift user with tens of thousands of photos, I want the new UI to stay smooth, so that the modern look does not make the app slow.

#### Acceptance Criteria

1. THE Thumbnail_Loader SHALL decode and scale every thumbnail on a background thread, perform no image decoding or scaling on the GUI thread, and deliver each finished thumbnail to the GUI thread.
2. WHEN a Thumbnail_Tile or List_Row becomes visible (at least 1 pixel of the tile or row is inside the scroll area's viewport), THE Thumbnail_Loader SHALL queue a load request for that file only if the file's thumbnail is neither in the in-memory cache nor already queued or loading.
3. WHILE a thumbnail is queued or loading, THE Thumbnail_Tile or List_Row SHALL show a placeholder with the same width and height as the thumbnail, so that the layout does not shift when the thumbnail arrives.
4. WHEN a Thumbnail_Tile or List_Row scrolls fully out of the viewport before its thumbnail has started loading, THE Thumbnail_Loader SHALL remove the pending request for that file from its queue.
5. THE Thumbnail_Loader SHALL hold at most 2,000 thumbnails in its in-memory cache and, when adding a thumbnail would exceed 2,000 entries, SHALL evict the entry that was least recently added or read.
6. WHEN a Scan_Result with up to 50,000 files and 5,000 Duplicate_Groups is loaded, THE Duplicates_Page and Cleanup_Page SHALL each render, within 2 seconds of the user opening the Page, every Group_Card or List_Row that fits in the viewport, with file names shown and thumbnails either shown or replaced by placeholders, on a machine with a 4-core CPU and an SSD.
7. WHILE the user scrolls the Duplicates_Page or Cleanup_Page with a loaded Scan_Result of up to 50,000 files and thumbnails are loading in the background, THE FileSift SHALL keep each GUI event-loop iteration under 100 milliseconds.
8. THE Cleanup_Page SHALL display at most 20,000 List_Rows, taken from the files that match the current Cleanup_Page filters.
9. IF more than 20,000 files match the current Cleanup_Page filters, THEN THE Cleanup_Page SHALL show the total match count followed by "(showing first 20000)" in its status text, and when 20,000 or fewer files match, the Cleanup_Page SHALL show the total match count without that suffix.
10. IF the Thumbnail_Loader cannot produce a thumbnail for a file because the file is missing, unreadable, corrupt, or in an unsupported format, THEN THE Thumbnail_Tile or List_Row SHALL replace the placeholder with a fallback icon of the same size, and THE Thumbnail_Loader SHALL skip that file for further load attempts until a new Scan_Result is loaded.
11. WHEN the Thumbnail_Loader delivers a finished thumbnail, THE FileSift SHALL store the thumbnail in the cache and display the thumbnail only in Thumbnail_Tiles or List_Rows that currently represent that file, leaving tiles or rows reused for other files unchanged.

### Requirement 13: Themed dialogs and messages

**User Story:** As a FileSift user, I want confirmations and errors to match the new look, so that the app feels consistent and the safety prompts stay clear.

#### Acceptance Criteria

1. WHEN the user starts a Recycle_Bin_Operation or a Move_Operation, THE Confirm_Dialog SHALL open as a modal dialog that blocks input to the Main_Window until the dialog closes, use the Theme, and show a rounded card containing a title, a message, a primary Pill_Button labelled with the confirming action (for example "Move to Recycle Bin"), and a secondary Pill_Button labelled "Cancel".
2. WHEN the Confirm_Dialog opens, THE Confirm_Dialog SHALL give keyboard focus to the "Cancel" Pill_Button and make the "Cancel" Pill_Button the default button, so that pressing Enter, pressing Escape, or closing the dialog with the window close button closes the dialog without moving or deleting any file and without changing the current file selection.
3. WHEN the Confirm_Dialog opens for a Recycle_Bin_Operation, THE Confirm_Dialog SHALL state the number of files the operation will affect, their total size in the same human-readable size format used elsewhere in FileSift (for example "1.5 GB"), and that the files can be restored from the Recycle Bin.
4. IF a Recycle_Bin_Operation or Move_Operation fails for one or more files, THEN THE FileSift SHALL show an error Message_Dialog after the operation finishes that lists the error messages for the first 15 failed files, each naming the file and the reason it failed, states how many additional errors are not shown when more than 15 files failed, keeps the successfully processed files processed, and leaves the failed files on disk at their original location.
5. WHEN a Recycle_Bin_Operation or Move_Operation completes, THE FileSift SHALL show a result in the Status_Area of the Page where the operation started, stating the number of files successfully moved, the total size freed (for Recycle_Bin_Operations), and the number of files that failed (when at least one failed), and SHALL keep the result visible until the next action on that Page replaces it.
6. IF one or more files in a Recycle_Bin_Operation have Verdict "Keep" or at least one Important_Tag, THEN THE Confirm_Dialog SHALL include a warning that states how many of the affected files have Verdict "Keep" or an Important_Tag.
7. WHEN the Confirm_Dialog opens for a Move_Operation, THE Confirm_Dialog SHALL state the number of files the operation will affect and the full path of the destination Important_Folder.
8. WHEN FileSift shows an informational or warning message outside the Confirm_Dialog (for example missing scan folders or a failed file operation), THE FileSift SHALL show the message in a Message_Dialog with a title, a message, and one primary Pill_Button that closes the dialog; Status_Area results (criterion 5) and the non-blocking Theme save message (Requirement 15.7) are excluded.

### Requirement 14: Preserve safety behaviour

**User Story:** As a FileSift user, I want the redesign to keep every safety rule, so that I never lose a file I did not explicitly choose to delete.

#### Acceptance Criteria

1. THE FileSift SHALL delete files only by sending each file to the Windows Recycle Bin, and SHALL offer no action that permanently deletes a file.
2. WHEN the user starts a Recycle_Bin_Operation or Move_Operation, THE FileSift SHALL show the Confirm_Dialog with the content defined in Requirement 13.3 (Recycle_Bin_Operation) or Requirement 13.7 (Move_Operation) and the "Cancel" Pill_Button as the default button, perform the operation only after the user selects the confirming Pill_Button, and, if the user cancels or closes the Confirm_Dialog, keep every selected file in its original location and the selection unchanged.
3. THE Duplicates_Page and Cleanup_Page SHALL exclude Protected_Files from every Recycle_Bin_Operation and Move_Operation, SHALL prevent the user from marking or ticking a Protected_File, SHALL leave every Protected_File unmarked during Auto-select and "Tick all safe to delete", and SHALL label each Protected_File as protected in its Thumbnail_Tile or List_Row.
4. THE FileSift SHALL keep the existing scanning, duplicate detection, Keeper_Rule, classification, OCR and PDF text extraction behaviour unchanged, as verified by every existing core test in the Test_Suite other than the bill test removed under Requirement 2 passing with no changes to those tests, and by no behaviour changes to the scanner, features, duplicates, classify, pipeline and textextract modules.
5. IF the user tries to mark the last unmarked file in a Duplicate_Group, THEN THE Duplicates_Page SHALL keep that file unmarked and show the message defined in Requirement 9.6, with Protected_Files counted as unmarked.
6. IF sending a file to the Recycle Bin or moving a file fails, THEN THE FileSift SHALL leave that file in its original location, continue processing the remaining confirmed files, keep the failed file listed on the Page, and show the failed file paths with their failure reasons in the error Message_Dialog defined in Requirement 13.4.
7. WHEN the FileSift moves a file into a destination folder that already contains a file with the same name, THE FileSift SHALL keep the existing destination file unchanged and save the moved file under the original name with a numeric suffix " (n)" added before the extension, where n starts at 2 and increases by 1 until the name is unused, as defined in Requirement 4.6.

### Requirement 15: Optional light theme

**User Story:** As a FileSift user, I want the option of a light theme, so that I can use the app comfortably in bright rooms.

#### Acceptance Criteria

1. WHERE the Light_Theme is provided, THE Sidebar SHALL contain a single Theme_Toggle with exactly two states, Dark_Theme and Light_Theme, whose displayed state matches the Theme currently applied to FileSift.
2. WHERE the Light_Theme is provided, WHEN the user activates the Theme_Toggle, THE FileSift SHALL apply the other Theme to the Sidebar, all open Pages, and all open dialogs within 1 second, without a restart and without discarding any unsaved input, selection, or scroll position on those Pages and dialogs.
3. WHERE the Light_Theme is provided, WHEN the user switches Theme, THE FileSift SHALL save the chosen Theme to the `theme` setting in the SQLite `settings` table before the next application start, storing one of exactly two values that identify Dark_Theme or Light_Theme.
4. WHERE the Light_Theme is provided, WHEN FileSift opens a Page or dialog after a Theme switch, THE FileSift SHALL render that Page or dialog in the currently applied Theme.
5. WHERE the Light_Theme is provided, WHEN FileSift starts, THE FileSift SHALL apply the Theme saved in the `theme` setting before the Main_Window is first shown, and SHALL apply the Dark_Theme if no `theme` setting exists.
6. WHERE the Light_Theme is provided, IF the `theme` setting holds a value that does not identify Dark_Theme or Light_Theme, or the `settings` table cannot be read at startup, THEN THE FileSift SHALL start with the Dark_Theme applied and continue starting without a blocking error dialog.
7. WHERE the Light_Theme is provided, IF saving the `theme` setting fails, THEN THE FileSift SHALL keep the newly chosen Theme applied for the current session and show a non-blocking message indicating that the Theme choice could not be saved and will not persist after restart.

### Requirement 16: Platform, dependencies and tests

**User Story:** As the maintainer, I want the redesign to stay lightweight and tested, so that the app remains easy to install and safe to change.

#### Acceptance Criteria

1. WHEN `python run.py` is executed on Windows 10 or Windows 11 with Python 3.12 and the packages from `requirements.txt` installed (including PySide6 6.8.1), THE FileSift SHALL display the Main_Window without raising an unhandled exception.
2. THE FileSift SHALL build the UI with PySide6 Qt Widgets only, `requirements.txt` SHALL list no required package other than PySide6 6.8.1, Pillow, numpy and Send2Trash 1.8.3, and FileSift SHALL import or install no web view, Electron or QML runtime.
3. THE Test_Suite SHALL contain no test function that imports, calls or asserts on the removed bill or reminder modules or on any bill or reminder Page of the Main_Window.
4. WHEN the UI smoke test runs, THE UI smoke test SHALL create the Main_Window with the Qt platform set to offscreen (no window shown on screen), load a Scan_Result containing exactly one Duplicate_Group of three identical copies and one unrelated file, invoke Auto-select, and verify that exactly two of the three copies are marked, one copy remains unmarked, and the unrelated file is not marked.
5. WHEN the UI smoke test attempts to mark all three copies of the Duplicate_Group, THE UI smoke test SHALL verify that exactly two copies remain marked and at least one copy stays unmarked.
6. WHEN the UI smoke test triggers "Move to Recycle Bin" with the Confirm_Dialog stubbed to accept and the Recycle Bin call stubbed to report success, THE UI smoke test SHALL verify that the stubbed Recycle Bin call received exactly the two marked file paths, that zero Group_Cards remain on the Duplicates_Page, and that the Cleanup_Page then lists exactly four files.
7. WHEN the Test_Suite is run with `python tests/test_core.py` and `python tests/test_ui_smoke.py` on Windows, THE Test_Suite SHALL finish each script within 60 seconds with exit code 0, and IF any assertion fails, THEN the failing script SHALL exit with a non-zero exit code.
8. THE Test_Suite SHALL create its test files only inside a temporary directory, use an in-memory Store instead of the user's settings or cache, move no real file to the Recycle Bin, and remove the temporary directory when each test finishes, whether the test passes or fails.
