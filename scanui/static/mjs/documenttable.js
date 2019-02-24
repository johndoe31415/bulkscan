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

export class DocumentTable {
	constructor(documents, table) {
		this._documents = documents;
		this._table = table;
		this._filter = null;
		this._sorted_by = null;
		this._invert_sort = false;
	}

	get filter() {
		return this._filter;
	}

	set filter(new_filter) {
		this._filter = new_filter;
		this._reapply_filter();
	}

	_reapply_filter() {
		const tbody = this._table.querySelector("tbody");
		if (tbody == null) {
			return;
		}
		const doctable = this;
		tbody.querySelectorAll("tr").forEach(function(row) {
			const visible = row.doc.fulfills(doctable._filter);
			if (visible) {
				row.classList.remove("hidden");
			} else {
				row.classList.add("hidden");
			}
		});
	}

	_render_cell(doc, data_type) {
		const cell = document.createElement("td");
		if (data_type == "peer") {
			cell.innerHTML = doc.properties.peer;
		} else if (data_type == "docname") {
			cell.innerHTML = doc.properties.docname;
		} else if (data_type == "tags") {
			cell.innerHTML = doc.tags;
		} else if (data_type == "docdate") {
			cell.innerHTML = doc.properties.docdate;
		} else if (data_type == "pagecnt") {
			cell.innerHTML = doc.pages.length;
		} else if (data_type == "doctype") {
			cell.innerHTML = doc.properties.doctype;
		}
		return cell;
	}

	_repopulate_table() {
		/* TODO avoid reflow by creating fragment? */
		const tbody = this._documents[0].row.parentElement;
		for (const doc of this._documents) {
			tbody.append(doc.row);
		}
	}

	_mark_sorting_table_head() {

	}

	_sort_table_by(key) {
		const known_sort_functions = {
			docname:	(doc1, doc2) => doc1.properties.docname.localeCompare(doc2.properties.docname),
			peer:		(doc1, doc2) => doc1.properties.peer.localeCompare(doc2.properties.peer),
			docdate:	(doc1, doc2) => -doc1.properties.docdate.localeCompare(doc2.properties.docdate),
		};

		if (key in known_sort_functions) {
			const base_sort_function = known_sort_functions[key];
			if (key == this._sort_function) {
				this._invert_sort = !this._invert_sort;
			} else {
				this._invert_sort = false;
			}
			this._sort_function = key;
			this._mark_table_head();

			let sort_function = this._invert_sort ? (doc1, doc2) => -base_sort_function(doc1, doc2) : base_sort_function;
			this._documents.sort(sort_function);
			this._repopulate_table();
		}
	}

	_on_click_head(event) {
		const th_name = event.target.getAttribute("name");
		this._sort_table_by(th_name);
	}

	populate() {
		const documenttable = this;
		let data_types = [ ];
		const thead = this._table.querySelectorAll("thead th").forEach(function(cell) {
			data_types.push(cell.getAttribute("name"));
			cell.addEventListener("click", (event) => documenttable._on_click_head(event));
		});

		const tbody = document.createDocumentFragment();
		for (const doc of this._documents) {
			const row = document.createElement("tr");
			for (const data_type of data_types) {
				row.append(this._render_cell(doc, data_type));
			}
			row.doc = doc;
			doc.row = row;
			tbody.append(row);
		}
		this._reapply_filter();

		const doc_tbody = this._table.querySelector("tbody");
		doc_tbody.innerHTML = "";
		doc_tbody.append(tbody);
	}
}
