#!/bin/bash
#
# Bash script common template file

set -u

readonly SCRIPT_NAME="$(basename $0)"               # Name of this script file
readonly SCRIPT_DIR="$(cd $(dirname $0) && pwd)"    # Absolute path of a the directory of this script file
readonly SCRIPT_PATH="${SCRIPT_DIR}/${SCRIPT_NAME}" # Absolute path of this script file
readonly HEADER="$(basename $0): "
readonly SPACER="${HEADER//?/ }"
# readonly SPACER="$(echo "${HEADER}" | sed -r "s/./ /g")"

function usage() {
	cat << _EOT_
Usage:
	${SCRIPT_NAME} [-w width] [-s indent character] file

Description:
	テキストファイルを整形するスクリプト。
	ファイル先頭の改行と連続しない改行は無視され、連続する改行とファイル末尾の改行は1つの改行に変換される。
	ファイル末尾に改行がない場合も、1つの改行が追加される。
	その後、行頭に字下げを追加した上で、foldコマンドによる自動改行を行う。

Options:
	-w	幅を指定する。デフォルト値は80。
	-s	字下げに使用する空白文字を指定する。デフォルト値は半角スペース2つ。
	-h	このヘルプを表示する。
_EOT_
	exit 1
}

function error_message() {
	local orig_ifs=$IFS
	IFS=$'\n'

	local line
	read line
	echo "${HEADER}${line}" >&2
	while read line; do 
		echo "${SPACER}${line}" >&2
	done

	IFS=${orig_ifs}
}


input_file='/dev/stdin'
width=80
indent='  '

while getopts 'w:s:' opt; do
	case ${opt} in
		w ) width=${OPTARG} ;;
		s ) indent=${OPTARG} ;;
		h ) usage; exit ;;
	esac
done

shift $((OPTIND - 1))
if [[ $# -ge 1 ]]; then
	input_file=$1
fi

cat "${input_file}" | sed -z -r -e 's/([^\n])\n($|[^\n])/\1\2/g' -e 's/^\n+//g' -e 's/\n*$/\n/g' -e 's/\n+/\n/g' \
                    | sed -r -e "s/^/${indent}/g" \
                    | fold -w "${width}"
