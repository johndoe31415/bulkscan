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

export class PreviewModal extends Modal {
	constructor(thumbnail) {
		super("/static/html/modal_preview_image.html", "/static/css/modal_preview_image.css");
		this._thumbnail = thumbnail;
	}

	keydown(event) {
		if (event.code == "Escape") {
			this._finish(true);
		}
	}

	_initialize() {
		this.div.querySelector("img").src = "/incoming/image/" + this._thumbnail.filename;
		this.div.querySelector("#filename").innerText = this._thumbnail.filename;
	}
}
