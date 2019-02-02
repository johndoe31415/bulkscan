#!/usr/bin/python3
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
import sys
import json

base_dir = os.path.realpath(os.path.dirname(__file__))
config_json_filename = os.path.realpath(base_dir + "/config.json")
with open(config_json_filename) as f:
	config = json.load(f)
config["thumb_dir"] = os.path.realpath(config["thumb_dir"])
config["incoming_dir"] = os.path.realpath(config["incoming_dir"])

from scanui import app, ctrlr
app.config.update(config = config)
ctrlr.set_config(config)

application = app
if __name__ == "__main__":
	application.run()
