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

export class Modal {
	constructor(template_uri, css_uri) {
		this._template_uri = template_uri;
		this._css_uri = css_uri;
		this._div = null;
		this._css = null;
		this._finished_callback = null;
	}

	get div() {
		return this._div;
	}

	_finish(resultcode, resulttext) {
		if (!this._finished_callback) {
			console.log("Cannot _finish() modal without finish callback.");
			return;
		}

		if (!this._mayfinish(resultcode, resulttext)) {
			/* For example: Form plausibilization failed */
			return false;
		}

		/* Collect results only if successfully created modal */
		const data = resultcode ? this._collect() : null;

		/* Teardown presentation */
		this._div.remove();
		this._css.remove();

		/* Return result to caller */
		this._finished_callback({
			resultcode: resultcode,
			resulttext: resulttext,
			data: data,
		});
		this._finished_callback = null;
	}

	_initialize() {
		/* Should be overwritten by child class if needed */
	}

	_collect() {
		/* Should be overwritten by child class if needed */
	}

	_show() {
		/* Should be overwritten by child class if needed */
	}

	_mayfinish(resultcode, resulttext) {
		/* Should be overwritten by child class if needed */
		return true;
	}

	keydown(event) {
		/* Should be overwritten by child class if needed */
	}

	run(finished_callback) {
		const modal = this;
		this._finished_callback = finished_callback;

		/* Instanciate by loading the template */
		fetch(this._template_uri).then(function(response) {
			if (response.status == 200) {
				return response.text();
			} else {
				/* Failed. */
				modal._finish(false, "Could not fetch template.");
			}
		}).then(function(template_data) {
			/* We got the template. Also load the CSS */
			const css = document.createElement("link");
			css.rel = "stylesheet";
			css.href = modal._css_uri;
			modal._css = css;
			document.head.append(css);

			const div = document.createElement("div");
			div.classList.add("modal");
			div.innerHTML = template_data;
			div.querySelectorAll("button.modal-ok").forEach(function(button) {
				button.onclick = function() { modal._finish(true, "OK button"); };
			});
			div.querySelectorAll("button.modal-cancel").forEach(function(button) {
				button.onclick = function() { modal._finish(false, "Cancel button"); };
			});

			modal._div = div;

			/* Initialize by child class */
			modal._initialize();

			/* Show modal */
			document.body.append(div);

			/* Change focus if needed */
			modal._show();
		});

	}
}
