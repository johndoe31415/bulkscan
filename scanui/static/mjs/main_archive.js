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
import {DocumentTable} from "/static/mjs/documenttable.js";
import {Document} from "/static/mjs/document.js";

const elem_content = document.querySelector("#content");
const elem_showarea = document.querySelector("#showarea");
let active_modal = null;
let thumbnails = null;
let documenttable = null;

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

document.addEventListener("keydown", document_keydown_handler, false);
document.querySelectorAll(".actionlink").forEach(function(link) {
	if (link.getAttribute("action")) {
		link.addEventListener("click", () => perform_action(link.getAttribute("action")), false);
	}
});

fetch("/document").then(function(response) {
	if (response.status == 200) {
		return response.json();
	}
}).then(function(document_list) {
	let documents = [ ];
	for (const [ uuid, document_data ] of Object.entries(document_list)) {
		const doc = new Document(uuid, document_data);
		documents.push(doc);
	}
	documenttable = new DocumentTable(documents, document.querySelector("#document_table"));
	documenttable.populate();
	elem_content.style.display = "";
});
