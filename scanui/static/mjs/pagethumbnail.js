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

export class PageThumbnail {
	constructor(container, filename, tid, options) {
		this._container = container;
		this._filename = filename;
		this._tid = tid;
		this._options = options;
		this._div = null;
		this._loaded = null;
		this._dragsrc = null;
	}

	get container() {
		return this._container;
	}

	get tid() {
		return this._tid;
	}

	get filename() {
		return this._filename;
	}

	get options() {
		return this._options;
	}

	get div() {
		return this._div;
	}

	load() {
		if (!this._loaded) {
			this.loaded = true;
			const img = this._div.querySelector("img");
			img.src = img.getAttribute("actual_src");
		}
	}

	_on_click(event) {
		/* this == div */
		if (event.path[0].nodeName == "BUTTON") {
			/* Clicked on one of the buttons, ignore this one. */
			return;
		}

		const thumbnail = this.thumbnail;
		if (event.ctrlKey) {
			/* Callback */
			if (thumbnail.options.ctrl_click_handler) {
				thumbnail.options.ctrl_click_handler(thumbnail);
			}
		} else if (event.shiftKey) {
			if (thumbnail.options.selectable) {
				/* Range click */
				thumbnail.container.range_select(thumbnail);
			}
		} else {
			if (thumbnail.options.selectable) {
				/* Regular mouse click */
				this.classList.toggle("selected");
				thumbnail.container.last_clicked = thumbnail;
			}
		}
	}

	_on_dragstart(event) {
		/* this == div */
		this.classList.add("dragging");
		this.thumbnail.container.drag_start(this);
	}

	_on_dragend(event) {
		/* this == div */
		this.classList.remove("dragging");
	}

	_on_dragenter(event) {
		/* this == img */
		this.parentElement.classList.add("dragover");
		event.preventDefault();
	}

	_on_dragover(event) {
		/* this == img */
		event.preventDefault();
	}

	_on_dragleave(event) {
		/* this == img */
		this.parentElement.classList.remove("dragover");
	}

	_on_drop(event) {
		/* this == img */
		const div = this.parentElement;
		div.classList.remove("dragover");
		div.thumbnail.container.drag_end(div);
	}

	_on_mouseleave(event) {
		this.container.zoom_img.style.display = "none";
	}

	_on_mousemove(event) {
		if (!event.ctrlKey) {
			this.container.zoom_img.style.display = "none";
			return;
		}
		const zoom_img = this.container.zoom_img;
		const target = "/incoming/image/" + this._filename;
		if (zoom_img.src != target) {
			zoom_img.src = target;
		}

		const div_css_width = 600;
		const div_css_height = 600;
		if (zoom_img.width != 0) {
			const x_ratio = event.offsetX / event.target.width;
			const x_left = (-x_ratio) * (zoom_img.width - div_css_width);
			zoom_img.style.left = x_left + "px";
		}
		if (zoom_img.height != 0) {
			const y_ratio = event.offsetY / event.target.height;
			const y_left = (-y_ratio) * (zoom_img.height - div_css_height);
			zoom_img.style.top = y_left + "px";
		}
		zoom_img.style.display = "";
	}

	_button_action(action) {
		const thumbnail = this;
		/* Disable button presses until we have a response */
		thumbnail.div.querySelector("div.buttons").classList.add("disabled");
		fetch("/incoming/action/" + action + "/" + this.filename, {
			method: "POST",
		}).then(function(response) {
			thumbnail.div.querySelector("div.buttons").classList.remove("disabled");
			if (response.status == 200) {
				thumbnail.reload();
			}
		});
	}

	select() {
		this.div.classList.add("selected");
	}

	deselect() {
		this.div.classList.remove("selected");
	}

	reload() {
		/* Reload thumbnail first */
		const imgnode = this.div.querySelector("img");
		const uri = imgnode.getAttribute("actual_src");
		imgnode.src = uri + "?ts=" + new Date().getTime();
		this._loaded = true;
	}

	create_div() {
		const thumbnail = this;
		this._div = document.createElement("div");
		this._div.thumbnail = this;
		this._div.className = "selectable_img";
		this._div.onclick = this._on_click;
		this._div.name = this._filename;
		this._div.setAttribute("tid", this._tid);

		const imgnode = document.createElement("img");
		imgnode.draggable = false;
		imgnode.setAttribute("actual_src", "/incoming/thumb/" + this._filename);
		if (this._options.lazy_loading) {
			imgnode.src = "#";
			this._loaded = false;
		} else {
			imgnode.src = "/incoming/thumb/" + this._filename;
			this._loaded = true;
		}
		imgnode.addEventListener("mouseleave", (event) => thumbnail._on_mouseleave(event), false);
		imgnode.addEventListener("mousemove", (event) => thumbnail._on_mousemove(event), false);
		this._div.appendChild(imgnode);

		const buttons_div = document.createElement("div");
		buttons_div.classList.add("buttons");
		buttons_div.setAttribute("tabIndex", "-1");
		for (let button_desc of [
			{
				text: "↶ ",
				handler: function() { thumbnail._button_action("rot270"); },
			},
			{
				text: "↻ ",
				handler: function() { thumbnail._button_action("rot180"); },
			},
			{
				text: "↷ ",
				handler: function() { thumbnail._button_action("rot90"); },
			},
		]) {
			const button = document.createElement("button");
			button.classList.add("actionbtn");
			button.innerHTML = button_desc.text;
			button.addEventListener("click", button_desc.handler, false);
			buttons_div.appendChild(button);
		}
		this._div.appendChild(buttons_div);

		if (this._options.draggable) {
			this._div.draggable = true;
			this._div.addEventListener("dragstart", this._on_dragstart, false);
			this._div.addEventListener("dragend", this._on_dragend, false);
			imgnode.addEventListener("dragenter", this._on_dragenter, false);
			imgnode.addEventListener("dragover", this._on_dragover, false);
			imgnode.addEventListener("dragleave", this._on_dragleave, false);
			imgnode.addEventListener("drop", this._on_drop, false);
		}
		return this._div;
	}
}

export class PageThumbnails {
	constructor(filename_list, options) {
		this._thumbnails = [ ];
		this._options = options;
		let tid = 0;
		for (let filename of filename_list) {
			const thumbnail = new PageThumbnail(this, filename, tid++, options);
			this._thumbnails.push(thumbnail);
		}
		this._innerdiv = null;
		this._zoom_img = null;
		this._drag_src = null;
		this._last_clicked = null;
	}

	get zoom_img() {
		return this._zoom_img;
	}

	get last_clicked() {
		return this._last_clicked;
	}

	set last_clicked(value) {
		this._last_clicked = value;
	}

	range_select(last_thumbnail) {
		let first_div, last_div;
		if (this._last_clicked != null) {
			if (this._last_clicked.div != last_thumbnail.div) {
				if ((this._last_clicked.div.compareDocumentPosition(last_thumbnail.div) & Node.DOCUMENT_POSITION_FOLLOWING) != 0) {
					first_div = this._last_clicked.div.nextSibling;
					last_div = last_thumbnail.div;
				} else {
					first_div = last_thumbnail.div;
					last_div = this._last_clicked.div.previousSibling;
				}
			} else {
				first_div = last_thumbnail.div;
				last_div = last_thumbnail.div;
			}
		} else {
			first_div = this._thumbnails[0].div;
			last_div = last_thumbnail.div;
		}
		let current = first_div;
		while (current) {
			current.classList.toggle("selected");
			if (current == last_div) {
				break;
			}
			current = current.nextSibling;
		}

		this._last_clicked = last_thumbnail;
	}

	drag_start(source_div) {
		this._drag_src = source_div;
	}

	drag_end(dest_div) {
		const move_left_to_right = (this._drag_src.compareDocumentPosition(dest_div) & Node.DOCUMENT_POSITION_FOLLOWING) != 0;
		if (move_left_to_right) {
			this._drag_src.parentElement.insertBefore(this._drag_src, dest_div.nextSibling);
		} else {
			this._drag_src.parentElement.insertBefore(this._drag_src, dest_div);
		}
	}

	_observe_callback(observer_entries) {
		for (const observer_entry of observer_entries) {
			if (!observer_entry.isIntersecting) {
				continue;
			}
			observer_entry.target.thumbnail.load();
		}
	}

	populate_container(container_div) {
		this._innerdiv = document.createElement("div");
		this._innerdiv.classList.add("thumbnail_container");
		this._innerdiv.collection = this;
		const observer_options = {
			root: null,
			rootMargin: "0px",
			threshold: 0.01,
		};
		const observer = this._options.lazy_loading ? new IntersectionObserver(this._observe_callback, observer_options) : null;
		for (var thumbnail of this._thumbnails) {
			const thumb_div = thumbnail.create_div();
			this._innerdiv.appendChild(thumb_div);
			if (observer) {
				observer.observe(thumb_div);
			}
		}

		const zoom_div = document.createElement("div");
		zoom_div.classList.add("zoompreview");

		const zoom_img = document.createElement("img");
		zoom_img.setAttribute("src", "");
		zoom_img.classList.add("zoompreview");
//		zoom_img.style.display = "none";
		this._zoom_img = zoom_img;
		zoom_div.appendChild(zoom_img);
		this._innerdiv.appendChild(zoom_div);

		container_div.innerHTML = "";
		container_div.appendChild(this._innerdiv);
	}

	load_all() {
		for (let thumbnail of this._thumbnails) {
			thumbnail.load();
		}
	}

	deselect_all() {
		this._innerdiv.querySelectorAll("div.selected").forEach(function(div) {
			div.classList.remove("selected");
		});
		this._last_clicked = null;
	}

	remove_selected() {
		this._innerdiv.querySelectorAll("div.selected").forEach(function(div) {
			div.remove();
		});
		const remaining_thumbnails = [ ];
		this._innerdiv.querySelectorAll("div.selectable_img").forEach(function(div) {
			remaining_thumbnails.push(div.thumbnail);
		});
		this._thumbnails = remaining_thumbnails;
		this._last_clicked = null;
	}

	get_filenames() {
		var filenames = [ ];
		this._innerdiv.querySelectorAll("div.selectable_img").forEach(function(div) {
			filenames.push(div.thumbnail.filename);
		});
		return filenames;
	}

	get_selected_filenames() {
		var filenames = [ ];
		this._innerdiv.querySelectorAll("div.selected").forEach(function(div) {
			filenames.push(div.thumbnail.filename);
		});
		return filenames;
	}

	get_last_selected() {
		let last_selected = null;
		this._innerdiv.querySelectorAll("div.selected").forEach(function(div) {
			last_selected = div;
		});
		if (last_selected) {
			return last_selected.thumbnail;
		} else {
			return null;
		}
	}

	selection_add_next() {
		if (this._thumbnails.length == 0) {
			return;
		}
		const last_selected = this.get_last_selected();
		if (last_selected == null) {
			this._thumbnails[0].select();
		} else {
			const next = last_selected.div.nextSibling.thumbnail;
			if (next) {
				next.select();
			}
		}
	}

	selection_remove_last() {
		const last_selected = this.get_last_selected();
		if (last_selected) {
			last_selected.deselect();
		}
	}
}
