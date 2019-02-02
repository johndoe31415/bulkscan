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

class Tools():
	@classmethod
	def cmdline(cls, cmd, env = None):
		if env is None:
			env = { }
		else:
			env = dict(env)

		def escape(text):
			if (" " in text) or ("\"" in text) or ("'" in text) or (";" in text) or ("&" in text) or ("*" in text):
				return "'%s'" % (text.replace("'", "\'"))
			else:
				return text
		command = " ".join(escape(arg) for arg in cmd)

		if env is None:
			return command
		else:
			env_string = " ".join("%s=%s" % (key, escape(value)) for (key, value) in sorted(env.items()))
			return (env_string + " " + command).lstrip()

