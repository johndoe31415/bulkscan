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

import {Modal} from "/static/mjs/modal.js";
import {PageThumbnails} from "/static/mjs/pagethumbnail.js";
import {PreviewModal} from "/static/mjs/modal_preview.js";
import {register_plausibilization} from "/static/mjs/plausibilization.js";

export class CreateDocumentModal extends Modal {
	constructor(filenames) {
		super("/static/html/modal_create_document.html", "/static/css/modal_create_document.css");
		this._filenames = filenames;
		this._thumbnails = null;
		this._active_modal = null;
		this._autocomplete_data = null;
	}

	_autocomplete_simple(term, suggestion_source) {
		const lc_term = term.toLowerCase();
		const suggestion = [ ];
		for (const tag of suggestion_source) {
			if (tag.toLowerCase().startsWith(lc_term)) {
				suggestion.push(tag);
			}
		}
		return suggestion;
	}

	_autocomplete_peer(term, suggest) {
		suggest(this._autocomplete_simple(term, Object.keys(this._autocomplete_data["docname_by_peer"])));
	}

	_autocomplete_docname(term, suggest) {
		const peer = this.div.querySelector("#create_peer").value;
		if (peer in this._autocomplete_data["docname_by_peer"]) {
			suggest(this._autocomplete_simple(term, this._autocomplete_data["docname_by_peer"][peer]));
		}
	}

	_autocomplete_tags(term, suggest) {
		suggest(this._autocomplete_simple(term, this._autocomplete_data["tag"]));
	}

	_create_autocompleter(element, choices) {
		const auto_complete_tags = new autoComplete({ selector: element, minChars: 1, delay: 0, source: function(term, suggest) {
			term = term.toLowerCase();
			var matches = [ ];
			for (let i = 0; i < choices.length; i++) {
				if (~choices[i].toLowerCase().indexOf(term)) {
					matches.push(choices[i]);
				}
			}
			suggest(matches);
		}});
	}

	keydown(event) {
		if (this._active_modal) {
			this._active_modal.keydown(event);
		} else {
			if (event.code == "Escape") {
				this._finish(false);
			} else if ((event.code == "Enter") && (!event.ctrlKey)) {
				if (document.activeElement && (document.activeElement.id == "create_tags")) {
					const tag_content = document.querySelector("#create_tags").value;
					if (tag_content != "") {
						const tag_span = document.createElement("span");
						tag_span.classList.add("tag");
						tag_span.innerText = tag_content;
						tag_span.onclick = function() {
							tag_span.remove();
						}
						document.querySelector("#create_tags_text").append(tag_span);
					}
					document.querySelector("#create_tags").value = "";
				}
			} else if ((event.code == "Enter") && event.ctrlKey) {
				/* Ctrl-Enter: try to close dialog */
				this._finish(true);
			}
		}
	}

	_ctrl_click_thumbnail(thumbnail) {
		const create_doc_modal = this;
		this._active_modal = new PreviewModal(thumbnail);
		this._active_modal.run(function(result) {
			create_doc_modal._active_modal = null;
		});

	}

	_mayfinish(resultcode, resulttext) {
		if (resultcode) {
			/* If we want to close successfully, all forms need to be plausibilized */
			let bad_element = null;
			this.div.querySelectorAll(".plausibilize").forEach(function(element) {
				if (!element.plausibilize().ok) {
					if (bad_element == null) {
						bad_element = element;
					}
				}
			});
			if (bad_element) {
				bad_element.focus();
			}
			return bad_element == null;
		}
		return true;
	}

	_collect() {
		const results = {
			"tags": [ ],
			"files": this._thumbnails.get_filenames(),
			"attrs": { },
		};
		this.div.querySelectorAll(".collect").forEach(function(element) {
			const key = element.name;
			const value = element.plausibilizer ? element.plausibilizer().machine_readable : element.value;
			results["attrs"][key] = value;
		});
		this.div.querySelectorAll("#create_tags_text span").forEach(function(element) {
			results["tags"].push(element.innerText);
		});
		return results;
	}

	_initialize() {
		const create_doc_modal = this;
		const options = {
			selectable:	false,
			lazy_loading: false,
			ctrl_click_handler: (thumbnail) => this._ctrl_click_thumbnail(thumbnail),
			draggable: true,
		};

		this._thumbnails = new PageThumbnails(this._filenames, options);
		this._thumbnails.populate_container(this._div.querySelector(".container"));
		this.div.querySelector("#create_pagecnt").innerText = this._filenames.length;

		fetch("/autocompletion").then(function(response) {
			if (response.status == 200) {
				return response.json();
			}
		}).then(function(autocomplete_data) {
			create_doc_modal._autocomplete_data = autocomplete_data;
			new autoComplete({ selector: create_doc_modal.div.querySelector("#create_peer"), minChars: 1, delay: 0, source: (term, suggest) => create_doc_modal._autocomplete_peer(term, suggest) });
			new autoComplete({ selector: create_doc_modal.div.querySelector("#create_docname"), minChars: 0, delay: 0, source: (term, suggest) => create_doc_modal._autocomplete_docname(term, suggest), cache: false });
			new autoComplete({ selector: create_doc_modal.div.querySelector("#create_tags"), minChars: 1, delay: 0, source: (term, suggest) => create_doc_modal._autocomplete_tags(term, suggest) });
		});

		this.div.querySelectorAll(".plausibilize").forEach(function(element) { register_plausibilization(element, create_doc_modal.div); });
	}

	_show() {
		this.div.querySelector("#create_peer").focus();
	}
}
