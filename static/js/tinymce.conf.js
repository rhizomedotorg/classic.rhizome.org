tinyMCE.init({
    mode : "specific_textareas",
    editor_selector : "mce-editor",
    theme : "advanced",
    plugins : "paste, inlinepopups, fullscreen", 
            
    // Theme options - button# indicated the row# only
    theme_advanced_buttons1 : "bold,italic,underline,strikethrough,blockquote,sub,sup,|,justifyleft,justifycenter,justifyright,|,fontsizeselect,|,bullist,numlist,|,forecolor,removeformat,hr,link,unlink,anchor,|,code,pasteword,|,undo,redo,fullscreen",
    theme_advanced_toolbar_location : "top",
    theme_advanced_toolbar_align : "left",
    theme_advanced_statusbar_location : "bottom",

    entity_encoding : "raw",
    add_unload_triggers : false,
    remove_linebreaks : false,
    inline_style : false,
    convert_fonts_to_spans : false,
    convert_urls : false, 
    extended_valid_elements : "inline[type|id|title],iframe[src|frameborder|alt|title|width|height|align|name|allowfullscreen]",
    custom_elements : "inline",
    paste_auto_cleanup_on_paste : true,
    fullscreen_new_window : true,

    width : "880",
    height : "500",
});