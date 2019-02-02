/*
	bulkscan - Document scanning and maintenance solution
	Copyright (C) 2019-2019 Johannes Bauer

	This file is part of bulkscan.

	bulkscan is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; this program is ONLY licensed under
	version 3 of the License, later versions are explicitly excluded.

	bulkscan is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with bulkscan; if not, write to the Free Software
	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

	Johannes Bauer <JohannesBauer@gmx.de>
*/

import {PageThumbnails} from "/static/mjs/pagethumbnail.js";
import {PreviewModal} from "/static/mjs/modal_preview.js";
import {CreateDocumentModal} from "/static/mjs/modal_create_document.js";

const elem_content = document.querySelector("#content");
const elem_showarea = document.querySelector("#showarea");
let active_modal = null;
let thumbnails = null;

function send_delete_images(filelist) {
	fetch("/incoming", {
		method: "DELETE",
		headers: {
			"Accept":		"application/json",
			"Content-Type":	"application/json",
		},
		body: JSON.stringify(filelist),
	});
	thumbnails.remove_selected();
}

function send_create_document(document_data) {
	fetch("/document", {
		method: "POST",
		headers: {
			"Accept":		"application/json",
			"Content-Type":	"application/json",
		},
		body: JSON.stringify(document_data),
	});
	thumbnails.remove_selected();
}

function action_create_document() {
	active_modal = new CreateDocumentModal(thumbnails.get_selected_filenames());
	active_modal.run(function(result) {
		if (result["resultcode"]) {
			/* Create document! */
			send_create_document(result["data"]);
		}
		active_modal = null;
	});
}

function action_deselect_selected_images() {
	thumbnails.deselect_all();
}

function action_delete_selected_images() {
	send_delete_images(thumbnails.get_selected_filenames());
}

function document_keydown_handler(event) {
	if (active_modal != null) {
		active_modal.keydown(event);
	} else {
		if ((event.code == "KeyX") && (event.ctrlKey)) {
			/* Ctrl-X: Deselect selected images */
			action_deselect_selected_images();
		} else if ((event.code == "KeyZ") && (event.ctrlKey)) {
			/* Ctrl-Y: Make new document */
			action_create_document();
		} else if (event.code == "Delete") {
			/* Delete key: Delete selected images */
			action_delete_selected_images();
		} else if (event.key == "+") {
			/* Plus key: Add next */
			thumbnails.selection_add_next();
		} else if (event.key == "-") {
			/* Minus key: Remove last */
			thumbnails.selection_remove_last();
		}
	}
}

function action_load_all_thumbnails() {
	thumbnails.load_all();
}

function ctrl_click_thumbnail(thumbnail) {
	/* Control-click, show preview */
	active_modal = new PreviewModal(thumbnail);
	active_modal.run(function(result) {
		active_modal = null;
	});
}

function perform_action(action) {
	const known_actions = {
		create_document:				action_create_document,
		deselect_selected_images:		action_deselect_selected_images,
		delete_selected_images:			action_delete_selected_images,
		load_all_thumbnails:			action_load_all_thumbnails,
	};
	if (action in known_actions) {
		const handler = known_actions[action];
		handler();
	} else {
		console.log("Unknown action:", action);
	}
}

document.addEventListener("keydown", document_keydown_handler, false);
document.querySelectorAll(".actionlink").forEach(function(link) {
	if (link.getAttribute("action")) {
		link.addEventListener("click", () => perform_action(link.getAttribute("action")), false);
	}
});

fetch("/incoming/list").then(function(response) {
	if (response.status == 200) {
		return response.json();
	}
}).then(function(filename_list) {
	const options = {
		selectable:	true,
		lazy_loading: true,
		ctrl_click_handler: ctrl_click_thumbnail,
	};
	thumbnails = new PageThumbnails(filename_list, options);
	thumbnails.populate_container(elem_showarea);
	elem_content.style.display = "";
});
