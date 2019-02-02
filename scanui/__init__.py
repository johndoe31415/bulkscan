#	bulkscan - Document scanning and maintenance solution
#	Copyright (C) 2019-2019 Johannes Bauer
#
#	This file is part of bulkscan.
#
#	bulkscan is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	bulkscan is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with bulkscan; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>

import os
import json
from flask import Flask, send_file, send_from_directory, jsonify, request, abort, redirect
from .Controller import Controller

app = Flask(__name__, static_folder = None)
ctrlr = Controller(app)

@app.route("/")
def index():
	return redirect("/static/html/incoming.html")

@app.route("/incoming/list")
def incoming_list():
	return jsonify(ctrlr.list_incoming())

# TODO SANITIZE FILENAME
@app.route("/incoming/thumb/<filename>")
def incoming_thumb(filename):
	thumb_filename = ctrlr.get_thumb(filename)
	if thumb_filename is None:
		# No such file or directory
		abort(404)
	return send_from_directory(ctrlr.config["thumb_dir"], thumb_filename, cache_timeout = 0)

@app.route("/incoming", methods = [ "DELETE" ])
def incoming_delete():
	return jsonify(ctrlr.delete_incoming(request.json))

# TODO SANITIZE FILENAME
@app.route("/incoming/action/<action>/<filename>", methods = [ "POST" ])
def incoming_action(action, filename):
	if action == "rot90":
		ctrlr.rotate(filename, 90)
	elif action == "rot180":
		ctrlr.rotate(filename, 180)
	elif action == "rot270":
		ctrlr.rotate(filename, 270)
	else:
		abort(400)
	return jsonify({ "status": "OK" })

# TODO SANITIZE FILENAME
@app.route("/incoming/image/<filename>")
def incoming_image(filename):
	return send_from_directory(ctrlr.config["incoming_dir"], filename, cache_timeout = 0)

@app.route("/autocompletion")
def autocompletion():
	return jsonify(ctrlr.acdb.get_all())

@app.route("/document", methods = [ "POST" ])
def document_create():
	indata = request.json
	return jsonify(ctrlr.create_document(indata["files"], indata["tags"], indata["attrs"]))
