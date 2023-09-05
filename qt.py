#!/usr/bin/env python
# coding:utf-8

"""
  Author: Massimiliano Belletti <max@belletti.net>
  Purpose: Helper for Quiver. Markdown export and Alfred search. 
  Created: 09/02/16
"""

import sys
import os
import json
import argparse
import re
import unicodedata
import string
import imghdr
import pathlib
from typing import Any
import logging


log = logging.getLogger(__file__)  # create logger
# log_handler = logging.FileHandler(__APPNAME__ + ".log")
log_handler = logging.StreamHandler(sys.stdout)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
log_handler.setFormatter(log_formatter)
log.addHandler(log_handler)
log.setLevel(logging.ERROR)

LIBRARY_PATH = "/changeme/Quiver.qvlibrary"


def quiver(path):
    """
    Extract Notebooks and Notes from quiver json
    """
    book_ext = ".qvnotebook"

    def _get_notebooks() -> dict:
        """
        Notebooks generator
        """
        for n in sorted(os.listdir(path)):
            if n.endswith(book_ext):
                d = json.loads(open(os.path.join(path, n, "meta.json")).read())
                d["notes"] = _get_notes(d)
                yield d

    def _get_notes(nb):
        """
        Notes generator
        """
        lpath = os.path.join(path, nb["uuid"] + book_ext)
        for n in sorted(os.listdir(lpath)):
            if ".json" in os.path.splitext(n):
                pass
            else:
                yield _get_note(nb, n)

    def _get_note(nb, notedir):
        "Note"
        lpath = os.path.join(path, nb["uuid"] + book_ext, notedir)
        n = json.loads(open(os.path.join(lpath, "meta.json")).read())
        n.update(
            dict(
                nb=nb["name"],
                nb_uuid=nb["uuid"],
            )
        )
        n.update(json.loads(open(os.path.join(lpath, "content.json")).read()))
        if "resources" in os.listdir(lpath):
            n.update({"resources": os.path.join(lpath, "resources")})
        return n

    return _get_notebooks()


def check_note(note, query) -> Any:
    """
    Filter note against query
    """
    if re.search(query, note["title"], flags=re.I):
        return note
    else:
        for c in note["cells"]:
            if re.search(query, c["data"], flags=re.I):
                return note


def alfred_search(query, lib=LIBRARY_PATH, on_notebooks=None, exclude_notebooks=None):
    """
    Perform a search and return Alfred formatted items
    """

    min_chars = 2

    tag_tpl = "<%(name)s%(attrs)s>%(value)s</%(name)s>"
    tag = lambda name, value, attrs=[]: tag_tpl % dict(
        name=name, value=value, attrs=(" " + " ".join(attrs) if attrs else "")
    )

    attr = lambda name, value: '%s="%s"' % (name, value)
    default_attrs = [attr("valid", "no")]

    def ae(title, sub, attrs=None):
        """
        Alfred element

        Represent a row in Alfred

        """
        attrs = attrs or default_attrs
        return tag(
            "item", "".join([tag("title", title), tag("subtitle", sub)]), attrs=attrs
        )

    def output(items):
        # items is a list tags
        xml_head = '<?xml version="1.0"?>'
        out = tag("items", "".join([i for i in items]))
        print(xml_head + out)

    note_ae = lambda note, attrs=default_attrs: ae(
        note["title"], note["uuid"], attrs=attrs
    )
    notes_to_alfred = lambda notes: output(
        [
            note_ae(
                n,
                attrs=[
                    attr("valid", "YES"),
                    attr("arg", "quiver:///notes/" + n["uuid"]),
                    attr("type", "file"),
                ],
            )
            for n in notes
        ]
    )

    if len(query) < min_chars:
        items = [
            ae(
                "Query too short",
                "The query needs to be at least " + str(min_chars) + " characters long",
            )
        ]
        output(items)
        return

    notebooks = quiver(lib)

    if exclude_notebooks:
        notebooks = [nb for nb in notebooks if not nb["uuid"] in exclude_notebooks]

    if on_notebooks:
        notebooks = [nb for nb in notebooks if nb["uuid"] in on_notebooks]

    notes = searchin_notebook(notebooks, query, exclude_notebooks)
    notes_to_alfred(notes)


def searchin_notebook(notebooks, query, exclude_notebooks=None):
    for nb in notebooks:
        if exclude_notebooks:
            if not nb["uuid"] in exclude_notebooks:
                for n in searchin_notes(nb["notes"], query):
                    yield n
        else:
            for n in searchin_notes(nb["notes"], query):
                yield n


def searchin_notes(notes, query):
    _ = []
    for n in notes:
        c = check_note(n, query)
        if c:
            _.append(n)
    return _


def md_export(notebooks, folder, index=True):
    """Export quiver contents in markdown"""

    def create_index(nb_index, nb, sane, nf):
        nb_index.append("[{}]({})\n".format(nb["name"], sane(nb["name"]) + "/index.md"))
        index = []
        for kk in nb["notes"]:
            n = nb["notes"][kk]
            index.append("[{}]({})\n".format(n["title"], sane(n["title"]) + ".md"))
        with open(os.path.join(nf, "index.md"), mode="wb") as f:
            f.write("[Notebooks](../index.md)\n\n".encode("utf8"))
            f.write("# Index\n\n---\n".encode("utf8"))
            h = None
            for kk in sorted([i.lower() for i in index]):
                if h != kk[1].lower():
                    h = kk[1].lower()
                    f.write("## {}\n".format(h).encode("utf8"))

                f.write("- {}\n".format(kk).encode("utf8"))

    validFilenameChars = "-_.(){}{}".format(string.ascii_letters, string.digits)

    def sane(filename):
        cleanedFilename = (
            unicodedata.normalize("NFKD", filename)
            .encode("ASCII", "ignore")
            .decode("ascii")
            .replace(" ", "_")
        )
        return "".join(c for c in cleanedFilename if c in validFilenameChars)

    def check_fname(fname):
        i = 0
        name = fname
        while os.path.exists(name):
            i += 1
            name = (
                os.path.splitext(fname)[0] + "_" + str(i) + os.path.splitext(fname)[1]
            )
        return name

    url_vendor = "/Applications/Quiver.app/Contents/Resources/dist/vendor"

    js_include = b"""\n<div>
    <script src="http://code.jquery.com/jquery-1.4.2.min.js"></script>
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>

    <script src="../.resources/vendor/raphael-min.js"></script>
    <script src="../.resources/vendor/underscore-min.js"></script>
    <script src="../.resources/vendor/sequence-diagram-min.js"></script>
    <script src="../.resources/vendor/flowchart.min.js"></script>
</div>
    """

    tpl_flow = b"""\n<div>
    <script>
        var diagram = flowchart.parse(document.getElementById('flowtext').innerText);
        diagram.drawSVG('flow');
    </script>
</div>
    """
    tpl_seq = b"""\n<div>
    <script>
        $(".sequence").sequenceDiagram({theme: 'simple'});
    </script>
</div>
    """

    def get_tree():
        return {
            nb["uuid"]: {
                "name": nb["name"],
                "notes": {n["uuid"]: n for n in nb["notes"]},
            }
            for nb in notebooks
        }

    node_tree = get_tree()

    def get_note_filename(n):
        try:
            return sane(n["title"]) + ".md"
        except Exception as e:
            log.error(e)
            raise e

    def search_in_tree(tree, k):
        for x in tree:
            if k in tree[x]["notes"]:
                return (
                    "../"
                    + sane(tree[x]["name"])
                    + "/"
                    + get_note_filename(tree[x]["notes"][k])
                )
        return None

    def fix_image_link(stringa):
        pattern = "(!\[IMAGE\]\(.*)(\ \=\d*x\d*)\)"
        ms = stringa
        m = re.findall(pattern, stringa)
        while m:
            ms = re.sub(pattern, "\g<1>)", ms)
            m = re.findall(pattern, ms)
            # print(ms)
        return ms

    re_note_link = "quiver-note-url/([a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12})"

    folder = folder or "notes"
    os.system('mkdir -p "%s"' % os.path.join(folder, ".resources"))

    os.system("cp -r %s %s" % (url_vendor, os.path.join(folder, ".resources")))

    nb_index = []
    for k in node_tree:
        nb = node_tree[k]
        log.debug(nb["name"])
        nf = os.path.join(folder, sane(nb["name"]))
        os.system('mkdir -p "%s"' % nf)
        if index:
            create_index(nb_index, nb, sane, nf)
        for kk in nb["notes"]:
            n = nb["notes"][kk]
            log.debug(n["title"])
            resources = n.get("resources")
            resources_path = pathlib.Path(nf) / "resources"
            resources_renamed = {}
            if resources:
                os.system('cp -r "%s" "%s"' % (n["resources"], nf))
                note_resources = resources_path.glob("*")
                for resource in note_resources:
                    if not resource.suffix:
                        ext = imghdr.what(resource)
                        if ext:
                            _ = resource.with_suffix("." + ext)
                            resources_renamed[resource] = _
                            resource.rename(_)

            j_included = False
            fname = check_fname(os.path.join(nf, sane(n["title"]) + ".md"))
            with open(fname, mode="wb") as f:
                if index:
                    f.write("[Index](index.md)\n\n".encode("utf8"))
                    f.write(f'# {n["title"]} \n\n'.encode("utf8"))
                if n["tags"]:
                    f.write("tags: [".encode("utf8"))
                    f.write(", ".join([f"`{t}`" for t in n["tags"]]).encode("utf8"))
                    f.write("]".encode("utf8"))
                    f.write("\n\n".encode("utf8"))
                for c in n["cells"]:
                    # pattern = "\ \=.*x\d*"

                    s = c["data"].replace("quiver-image-url", "resources")

                    # s = re.sub(pattern, "", s)
                    s = fix_image_link(s)
                    for r in resources_renamed:
                        s = s.replace(r.name, resources_renamed[r].name)
                    s = s.replace("quiver-file-url", "resources")
                    links = re.findall(re_note_link, s, re.I)
                    for l in links:
                        if not l in nb["notes"]:
                            x = search_in_tree(node_tree, l)
                            s = s.replace("quiver-note-url/" + l, x)
                        else:
                            s = s.replace(
                                "quiver-note-url/" + l,
                                get_note_filename(nb["notes"].get(l, "")),
                            )
                    s += "\n"
                    if c["type"] == "code":
                        s = "```\n" + s + "\n```"
                        f.write(s.encode("utf8"))
                    elif c["type"] == "diagram":
                        if not j_included:
                            f.write(js_include)
                            j_included = True
                        if c["diagramType"] == "sequence":
                            s = '\n<div class="sequence">' + s + "</div>\n"
                            f.write(s.encode("utf8"))
                        elif c["diagramType"] == "flow":
                            f.write(
                                str(
                                    '\n<div id="flowtext">'
                                    + s.replace("\n", "<br>")
                                    + "</div>\n"
                                ).encode("utf8")
                            )
                            f.write('\n<div id="flow"></div>\n'.encode("utf8"))
                            f.write(tpl_flow)
                    else:
                        f.write(s.encode("utf8"))
                if j_included:
                    f.write(tpl_seq)

        if index:
            with open(os.path.join(folder, "index.md"), mode="wb") as f:
                f.write("# Notebooks\n\n".format(n).encode("utf8"))
                for n in sorted(nb_index):
                    f.write("- {}\n".format(n).encode("utf8"))


def main():
    parser = argparse.ArgumentParser(description="Quiver helper")
    parser.add_argument("-l", "--list", help="List notebooks", action="store_true")
    parser.add_argument(
        "-q", "--query", help="Search <query> in notes", default=".*", type=str
    )
    parser.add_argument(
        "-n",
        "--notebooks",
        help="""Restrict search in notebooks. Needs uuids space separated""",
        type=str,
    )
    parser.add_argument(
        "-e",
        "--exclude_notebooks",
        help="Exclude notebooks from search. Needs uuids space separated",
        type=str,
    )
    parser.add_argument("-x", "--export", help="Export to folder", default="", type=str)
    parser.add_argument(
        "-v", "--verbose", help="Verbose", default=False, action="store_true"
    )
    parser.add_argument(
        "-i", "--index", help="Create an index for each notebook", action="store_true"
    )
    parser.add_argument(
        "-L", "--library", help="Quiver library path", default=LIBRARY_PATH, type=str
    )
    args = parser.parse_args()

    if not os.path.exists(args.library):
        log.error("Quiver library not found. ")
        log.error("%s doesn't exists." % args.library)
        sys.exit(1)

    if args.verbose:
        log.setLevel(logging.INFO)

    notebooks = quiver(args.library)

    if args.exclude_notebooks:
        notebooks = [nb for nb in notebooks if not nb["uuid"] in args.exclude_notebooks]

    if args.notebooks:
        notebooks = [nb for nb in notebooks if nb["uuid"] in args.notebooks]

    if args.list:
        print(
            ",\n".join(
                [
                    str({k: nb[k] for k in nb if k != "notes"})
                    for nb in notebooks
                    if re.match(args.query, nb["name"])
                ]
            )
        )
    elif args.export:
        md_export(notebooks, args.export, index=args.index)
    else:
        notes = searchin_notebook(notebooks, args.query)
        if notes:
            print(
                ",\n".join(
                    [
                        str(
                            {
                                "uuid": n["uuid"],
                                "title": n["title"],
                                "notebook": n["nb"],
                            }
                        )
                        for n in notes
                    ]
                )
            )
            # print "\n".join([n['title'] + ':\n' + n['uuid'] for n in notes])
        else:
            print("Nothing found")


if __name__ == "__main__":
    main()
    sys.exit(0)
