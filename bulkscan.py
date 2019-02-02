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
import uuid
import json
import subprocess
import datetime
import glob
import re
import queue
import time
import threading
from Tools import Tools
from FriendlyArgumentParser import FriendlyArgumentParser

class ConversionJob():
	def __init__(self, infile, outfile, meta = None):
		self._infile = infile
		self._outfile = outfile
		self._meta = meta

	def start(self):
		jsonexif = json.dumps(self._meta)
		subprocess.check_call([ "convert", "-units", "PixelsPerInch", "-density", str(self._meta["resolution"]), "-comment", jsonexif, self._infile, self._outfile ])
		os.unlink(self._infile)

	def __str__(self):
		return "%s -> %s" % (self._infile, self._outfile)

class JobServer():
	def __init__(self, concurrent_jobs = 12):
		self._queue = queue.Queue()
		self._threads = [ threading.Thread(target = self._thread_function) for i in range(concurrent_jobs) ]
		self._quit = False
		for thread in self._threads:
			thread.start()

	def add(self, job):
		self._queue.put(job)

	def shutdown(self):
		self._quit = True
		while not self._queue.empty():
			time.sleep(1)

	def _thread_function(self):
		while True:
			try:
				job = self._queue.get(timeout = 0.1)
				job.start()
			except queue.Empty:
				if self._quit:
					break

class BatchScanner():
	def __init__(self, args):
		self._args = args
		with open(self._args.config_file) as f:
			self._config = json.load(f)
		try:
			os.makedirs(self._args.outdir)
		except FileExistsError:
			pass

		self._scan_id = 0
		regex = re.compile("^bulk_(?P<id>\d{5})")
		for filename in os.listdir(self._args.outdir):
			match = regex.match(filename)
			if match:
				match = match.groupdict()
				self._scan_id = max(self._scan_id, int(match["id"]))

		self._jobserver = JobServer(concurrent_jobs = 12)

	def scan_next_batch(self):
		batch_uuid = str(uuid.uuid4())

		scan_cmd = [ "scanimage", "--mode", self._args.mode, "--resolution", str(self._args.resolution), "--batch=" + self._args.tempdir + "/scan_" + batch_uuid + "_%05d.pnm" ] + self._config["scan_cmdline"]
		subprocess.call(scan_cmd)
		infiles = [ ]
		regex = re.compile("scan_" + batch_uuid + "_(?P<no>\d{5}).pnm")
		for filename in glob.glob(self._args.tempdir + "/scan_" + batch_uuid + "_?????.pnm"):
			match = regex.search(filename)
			match = match.groupdict()
			pageno = int(match["no"])
			infiles.append((pageno, filename))
		infiles.sort()

		now = datetime.datetime.utcnow()
		for (pageno, infile) in infiles:
			self._scan_id += 1
			outfile = self._args.outdir + "/bulk_%05d_%05d.png" % (self._scan_id, pageno)
			job = ConversionJob(infile = infile, outfile = outfile, meta = {
				"batch_uuid":		batch_uuid,
				"created_utc":		now.strftime("%Y-%m-%dT%H:%M:%SZ"),
				"resolution":		self._args.resolution,
				"mode":				self._args.mode,
			})
			self._jobserver.add(job)

	def run(self):
		while True:
			result = input("Ready to scan next batch (q to quit)...")
			result = result.strip()
			if result == "q":
				break
			self.scan_next_batch()
		self._jobserver.shutdown()

parser = FriendlyArgumentParser()
parser.add_argument("-c", "--config-file", metavar = "filename", type = str, default = "config.json", help = "Configuration file to read. Defaults to %(default)s.")
parser.add_argument("-o", "--outdir", metavar = "dirname", type = str, default = "output/", help = "Output directory to place files in. Defaults to %(default)s.")
parser.add_argument("-r", "--resolution", metavar = "dpi", type = int, default = 300, help = "Resolution to use in dots per inch, defaults to %(default)d dpi.")
parser.add_argument("-m", "--mode", choices = [ "gray" ], default = "gray", help = "Scan mode to use. Can be one of %(choices)s, defaults to %(default)s.")
parser.add_argument("-t", "--tempdir", metavar = "dirname", type = str, default = "/tmp", help = "Temporary directory to keep raw files. Defaults to %(default)s")
args = parser.parse_args(sys.argv[1:])

scanner = BatchScanner(args)
scanner.run()
