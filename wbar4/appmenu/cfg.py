# load the menu from a file: 0 No (desktop files will be used) - 1 Yes (need to be rebuild manually after each change)
MENU_FROM_FILE=0
# window position: "center" OR "x/y" (/ is the separator)
win_position="center"
# with or without window decoration: 0 with; 1 without
win_no_deco=1
# this program always on top: 0 no; 1 yes
win_on_top=0
# menu category icon size
menu_icon_size=36
# app icon size
menu_app_icon_size=36
# service menu icon size: exit, etc.
service_icon_size=20
# service menu border colour
service_border_color="gray"
# program used to add applications OR "" - full path
app_prog="./appmenu.py"
# program used to modify a desktop file OR ""
app_mod_prog=app_prog
# search field background colour: colour (in the form "#xxxxxx") OR ""
search_field_bg="#D6D3D3"
# this program width
menu_width=600
# to use with a compositor enabled: 0 no - 1 yes
with_compositor=0
# windows border radius
border_radius=15
# shadow blur radius
blur_radius=15
# shadow blur distance
blur_effect=10
# theme style: "" to use the default theme
theme_style=""
# icon theme: "" to use the default theme
icon_theme=""
# in the form "#XXXXXX" or "rgb(X, X, X)" or "colour name"
scroll_handle_col="#B5B5B5"
# highlight color - in the form "#rrggbb or "" for default #DF5E0B
item_highlight_color=""
# dialog width
DIALOGWIDTH=300
# terminal to use: "" for the default one if any
USER_TERMINAL=""
# show also programs not found in paths: 0 no - 1 yes
SHOW_ALL_PROG=1