// Startup variables
/* Define the bbCode tags object */
var bb_tags = new Object();
bb_tags["bold"] = new Array('[b]','[/b]');
bb_tags["italic"] =  new Array('[i]','[/i]');
bb_tags["underline"] = new Array('[u]','[/u]');
bb_tags["quote"] = new Array('[quote]','[/quote]');
bb_tags["left"] = new Array('[text=left]','[/text]');
bb_tags["right"] = new Array('[text=right]','[/text]');
bb_tags["center"] = new Array('[text=center]','[/text]');
bb_tags["code"] = new Array('[code]','[/code]');
bb_tags["unordered_list"] = new Array('[ul]','[/ul]');
bb_tags["list_item"] = new Array('[*]','[/*]');
bb_tags["image"] = new Array('[img]','[/img]');
bb_tags["url"] = new Array('[url]','[/url]');
bb_tags["qt"] = new Array('[qt]','[/qt]');
bb_tags["youtube"] = new Array('[youtube]','[/youtube]');
bb_tags["vimeo"] = new Array('[vimeo]', '[/vimeo]');
bb_tags["flash"] = new Array('[flash]', '[/flash]');
bb_tags["director"] = new Array('[drc]]','[/drc]');
bb_tags["size"] = new Array('[size=]','[/size]');
bb_tags["color"] = new Array('[color=]','[/color]');
bb_tags["hr"] = new Array('[hr /]','');

/** get bb code markup style from bbstyle object */
function get_bbstyle(input, tag){
	var target_textarea = input.getParent().getSiblings('textarea');
	if (tag != -1){
		bbfontstyle(target_textarea[0], bb_tags[tag][0], bb_tags[tag][1]);
	} else {
		insert_text('[*]');
		input.getParent().getSiblings('textarea').focus();
	}
}

function input_color(anchor, bbopen, bbclose){
	var target_textarea = anchor.getParents('fieldset').getChildren('textarea');
	console.log(anchor.getParents('fieldset').getChildren('textarea'));
    bbfontstyle(target_textarea[0][0], bbopen, bbclose);
}

/* Apply bbcodes*/
function bbfontstyle(target_textarea, bbopen, bbclose){
	var textarea = target_textarea;
	textarea.focus();

    if (textarea.selectionEnd && (textarea.selectionEnd - textarea.selectionStart > 0)){
		mozWrap(textarea, bbopen, bbclose);
		textarea.focus();
		return;
	}
	
	//The new position for the cursor after adding the bbcode
	var caret_pos = textarea.getCaretPosition();
	var new_pos = caret_pos + bbopen.length;		

	// Open tag
	insert_text(textarea, bbopen + bbclose);

	// Center the cursor when we don't have a selection
	// Gecko and proper browsers
	if (!isNaN(textarea.selectionStart)){
		textarea.selectionStart = new_pos;
		textarea.selectionEnd = new_pos;
	}	
	// IE
	else if (document.selection) {
		var range = textarea.createTextRange(); 
		range.move("character", new_pos); 
		range.select();
		storeCaret(textarea);
	}

	textarea.focus();
	return;
}

/* Insert text at position */
function insert_text(textarea, text, spaces, popup){
	if (spaces) {
		text = ' ' + text + ' ';
	}
	
	if (!isNaN(textarea.selectionStart)){
		var sel_start = textarea.selectionStart;
		var sel_end = textarea.selectionEnd;
		mozWrap(textarea, text, '')
		textarea.selectionStart = sel_start + text.length;
		textarea.selectionEnd = sel_end + text.length;
	} else if (textarea.createTextRange && textarea.caretPos) {
		if (baseHeight != textarea.caretPos.boundingHeight) {
			textarea.focus();
			storeCaret(textarea);
		}
		var caret_pos = textarea.caretPos;
		caret_pos.text = caret_pos.text.charAt(caret_pos.text.length - 1) == ' ' ? caret_pos.text + text + ' ' : caret_pos.text + text;
	} else {
		textarea.value = textarea.value + text;
	}
	
	if (!popup) {
		textarea.focus();
	}
}

function mozWrap(txtarea, open, close){
	var selLength = txtarea.textLength;
	var selStart = txtarea.selectionStart;
	var selEnd = txtarea.selectionEnd;
	var scrollTop = txtarea.scrollTop;

	if (selEnd == 1 || selEnd == 2) 
	{
		selEnd = selLength;
	}

	var s1 = (txtarea.value).substring(0,selStart);
	var s2 = (txtarea.value).substring(selStart, selEnd)
	var s3 = (txtarea.value).substring(selEnd, selLength);

	txtarea.value = s1 + open + s2 + close + s3;
	txtarea.selectionStart = selEnd + open.length + close.length;
	txtarea.selectionEnd = txtarea.selectionStart;
	txtarea.focus();
	txtarea.scrollTop = scrollTop;

	return;
}