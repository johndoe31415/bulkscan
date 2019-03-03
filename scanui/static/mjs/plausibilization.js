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

const month_names = {
	full: {
		1:	"Januar",
		2:	"Februar",
		3:	"März",
		4:	"April",
		5:	"Mai",
		6:	"Juni",
		7:	"Juli",
		8:	"August",
		9:	"September",
		10:	"Oktober",
		11:	"November",
		12:	"Dezember",
	},
	abbreviated: {
		1:	"Jan",
		2:	"Feb",
		3:	"Mär",
		4:	"Apr",
		5:	"Mai",
		6:	"Jun",
		7:	"Jul",
		8:	"Aug",
		9:	"Sep",
		10:	"Okt",
		11:	"Nov",
		12:	"Dez",
	},
	parse: {
		"jan":	1,
		"feb":	2,
		"mar":	3,
		"mär":	3,
		"apr":	4,
		"may":	5,
		"mai":	5,
		"jun":	6,
		"jul":	7,
		"aug":	8,
		"sep":	9,
		"oct":	10,
		"okt":	10,
		"nov":	11,
		"dec":	12,
		"dez":	12,
	},
};

const weekday_names = {
	full: {
		0:	"Sonntag",
		1:	"Montag",
		2:	"Dienstag",
		3:	"Mittwoch",
		4:	"Donnerstag",
		5:	"Freitag",
		6:	"Samstag",
	},
	abbreviated: {
		0:	"So",
		1:	"Mo",
		2:	"Di",
		3:	"Mi",
		4:	"Do",
		5:	"Fr",
		6:	"Sa",
	},
};

export function is_valid_date(year, month, day) {
	if ((month < 1) || (month > 12)) {
		return false;
	}
	if ((year < 1900) || (year > 2500)) {
		return false;
	}

	if (day != undefined) {
		const days_in_month = new Date(year, month, 0).getDate();
		if ((day < 1) || (day > days_in_month)) {
			return false;
		}
	}

	return true;
}

export function parse_date(datestr) {
	let year = null, month, day;
	let result;

	do {
		result = datestr.match(/^(\d+)\.(\d+)\.(\d+)$/);
		if (result) {
			day = result[1] | 0;
			month = result[2] | 0;
			year = result[3] | 0;
			break;
		}

		result = datestr.match(/^(\d+)-(\d+)-(\d+)$/);
		if (result) {
			day = result[3] | 0;
			month = result[2] | 0;
			year = result[1] | 0;
			break;
		}

		result = datestr.match(/^(\d{2})(\d{2})(\d{2})$/);
		if (result) {
			day = result[1] | 0;
			month = result[2] | 0;
			year = result[3] | 0;
			break;
		}

		result = datestr.match(/^(\d+)[-.]?([A-Za-zäöü]+)[-.]?(\d+)$/);
		if (result) {
			if (result[2] in month_names.parse) {
				day = result[1] | 0;
				month = month_names.parse[result[2].toLowerCase()];
				year = result[3] | 0;
			}
			break;
		}

		result = datestr.match(/^(\d+)\.(\d+)$/);
		if (result) {
			day = result[1] | 0;
			month = result[2] | 0;
			year = new Date().getFullYear();
			break;
		}

		result = datestr.match(/^(\d{2})(\d{2})$/);
		if (result) {
			day = result[1] | 0;
			month = result[2] | 0;
			year = new Date().getFullYear();
			break;
		}

		result = datestr.match(/^(\d+)-(\d+)$/);
		if (result) {
			day = result[2] | 0;
			month = result[1] | 0;
			year = new Date().getFullYear();
			break;
		}

	} while (false);

	if (year == null) {
		return null;
	} else {
		if (year < 100) {
			year += 2000;
		}
		if (is_valid_date(year, month, day)) {
			return {
				dtype:		"date",
				year:		year,
				month:		month,
				day:		day,
			};
		} else {
			return null;
		}
	}
}

export function format_date_german(date_data) {
	const jsdate = new Date(date_data["year"], date_data["month"] - 1, date_data["day"]);
	return weekday_names.abbreviated[jsdate.getDay()] + ", " + sprintf("%d.%d.%d (%s)", date_data["day"], date_data["month"], date_data["year"], month_names.abbreviated[date_data["month"]]);
}

function format_date_mr(date_data) {
	return sprintf("date:%04d-%02d-%02d", date_data["year"], date_data["month"], date_data["day"]);
}

export function parse_month(monthstr) {
	let year = null, month;
	let result;

	do {
		result = monthstr.match(/^(\d+)\.(\d+)$/);
		if (result) {
			month = result[1] | 0;
			year = result[2] | 0;
			break;
		}

		result = monthstr.match(/^(\d{2})(\d{2})$/);
		if (result) {
			month = result[1] | 0;
			year = result[2] | 0;
			break;
		}

		result = monthstr.match(/^(\d+)-(\d+)$/);
		if (result) {
			month = result[2] | 0;
			year = result[1] | 0;
			break;
		}

		result = monthstr.toLowerCase().match(/^([A-Za-zäöü]+)\s*(\d+)$/);
		if (result) {
			if (result[1] in month_names.parse) {
				month = month_names.parse[result[1].toLowerCase()];
				year = result[2] | 0;
			}
			break;
		}

		result = monthstr.toLowerCase().match(/^(\d+)\s*([A-Za-zäöü]+)$/);
		if (result) {
			if (result[2] in month_names.parse) {
				month = month_names.parse[result[2].toLowerCase()];
				year = result[1] | 0;
			}
			break;
		}

		result = monthstr.toLowerCase().match(/^([A-Za-zäöü]+)$/);
		if (result) {
			if (result[1] in month_names.parse) {
				month = month_names.parse[result[1].toLowerCase()];
				year = new Date().getFullYear();
			}
			break;
		}
	} while (false);

	if (year == null) {
		return null;
	} else {
		if (year < 100) {
			year += 2000;
		}
		if (is_valid_date(year, month)) {
			return {
				dtype:		"month",
				year:		year,
				month:		month,
			};
		} else {
			return null;
		}
	}
}

export function format_month_german(date_data) {
	return month_names.full[date_data["month"]] + " / " + date_data["month"] + "'" + date_data["year"];
}

function format_month_mr(date_data) {
	return sprintf("month:%04d-%02d", date_data["year"], date_data["month"]);
}

export function register_plausibilization(input_element, base_node) {
	const known_functions = {
		date: {
			parse: parse_date,
			format: format_date_german,
			format_mr: format_date_mr,
		},
		month: {
			parse: parse_month,
			format: format_month_german,
			format_mr: format_month_mr,
		},
		str: {
			parse: (x) => x,
			format: (x) => x,
			format_mr: (x) => x,
		}
	};
	const params = JSON.parse(input_element.getAttribute("plausibilize"));
	if (!(params["fnc"] in known_functions)) {
		console.log("Unknown function:", params);
		return;
	}
	if (!("allow_empty" in params)) {
		params["allow_empty"] = true;
	}
	if (!("show_formatted" in params)) {
		params["show_formatted"] = true;
	}

	const plausibilization_function = known_functions[params["fnc"]];
	const text_field = ("text_selector" in params) ? (base_node ? base_node : document).querySelector(params["text_selector"]) : null;

	function plausibilizer() {
		const current_value = input_element.value;
		const current_parsed_value = plausibilization_function["parse"](current_value);
		const value_is_empty = (current_value == "");
		const allow_empty = !!params["allow_empty"];
		const value_parsed_ok = (current_parsed_value != null);
		const okay = (allow_empty && (value_is_empty || value_parsed_ok)) || (!allow_empty && (!value_is_empty && value_parsed_ok));
		const formatted = (current_parsed_value != null) ? plausibilization_function["format"](current_parsed_value) : null;
		const machine_readable = (current_parsed_value != null) ? plausibilization_function["format_mr"](current_parsed_value) : null;
		const result = {
			"ok":					okay,
			"invalue":				current_value,
			"value":				current_parsed_value,
			"formatted":			formatted,
			"machine_readable":		machine_readable,
		};
		return result;
	}

	function plausibilize() {
		const result = plausibilizer();
		if (result.ok) {
			input_element.classList.remove("bad-input");
			if (text_field) {
				if (params["show_formatted"]) {
					text_field.innerText = (result.value != null) ? result.formatted : "";
				} else {
					text_field.innerText = "";
				}
			}
		} else {
			input_element.classList.add("bad-input");
			if (text_field) {
				if ((result.invalue == "") && (!params["allow_empty"])) {
					text_field.innerText = "Field may not be empty.";
				} else {
					text_field.innerText = "Syntax error.";
				}
			}
		}
		return result;
	}

	function event_plausibilize() {
		plausibilize();
	}

	input_element.plausibilizer = plausibilizer;
	input_element.plausibilize = plausibilize;
	input_element.addEventListener("input", event_plausibilize, false);
}
