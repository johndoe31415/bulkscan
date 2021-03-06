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

export class DocumentFilter {
	constructor() {
		this._conditions = [ ];
	}

	add_cond(cond) {
		this._conditions.push(cond);
	}

	check(doc) {
		let pass = true;
		for (const cond of this._conditions) {
			pass = pass && cond(doc);
			if (!pass) {
				break;
			}
		}
		return pass;
	}
}

export class Document {
	constructor(doc_uuid, document_metadata) {
		this._doc_uuid = doc_uuid;
		this._document_metadata = document_metadata;
	}

	get tags() {
		return this._document_metadata.tags;
	}

	get properties() {
		return this._document_metadata.properties;
	}

	get pages() {
		return this._document_metadata.pages;
	}

	fulfills(document_filter) {
		if (document_filter == null) {
			return true;
		}
		return document_filter.check(this);
	}
}
