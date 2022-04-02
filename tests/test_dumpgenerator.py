#!/usr/bin/env python3

# Copyright (C) 2011-2016 WikiTeam developers
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import os
import tempfile
import time
import unittest

import requests

from wikiteam3.dumpgenerator.api_info import ApiInfo
from wikiteam3.dumpgenerator.delay import delay
from wikiteam3.dumpgenerator.image import ImageDumper
from wikiteam3.dumpgenerator.page_titles import fetchPageTitles
from wikiteam3.dumpgenerator.user_agent import UserAgent
from wikiteam3.dumpgenerator.wiki_check import getWikiEngine


class TestDumpgenerator(unittest.TestCase):
    """Documentation
    http://revista.python.org.ar/1/html/unittest.html
    https://docs.python.org/2/library/unittest.html

    Ideas:
    - Check one wiki per wikifarm at least (page titles & images, with/out API)
    """

    def test_delay(self):
        """This test checks several delays"""

        print("\n", "#" * 73, "\n", "test_delay", "\n", "#" * 73)
        for i in [0, 1, 2, 3]:
            print("Testing delay:", i)
            config_for_index_php = {"delay": i}
            t1 = time.time()
            delay(config_for_index_php)
            t2 = time.time() - t1
            print("Elapsed time in seconds (approx.):", t2)
            self.assertTrue(t2 + 0.01 > i and t2 < i + 1)

    def test_getImages(self):
        """This test download the image list using API and index.php
        Compare both lists in length and file by file
        Check the presence of some special files, like odd chars filenames
        The tested wikis are from different wikifarms and some alone"""

        print("\n", "#" * 73, "\n", "test_getImages", "\n", "#" * 73)
        tests = [
            # Test fails on ArchiveTeam
            # with len(result_api) != image_count
            # [
            #     "https://wiki.archiveteam.org/index.php",
            #     "https://wiki.archiveteam.org/api.php",
            #     "Archive-is 2013-07-02 17-05-40.png",
            # ],
            [
                "https://wiki.archlinux.org/index.php",
                "https://wiki.archlinux.org/api.php",
                "Archstats2002-2011.png",
            ],
            # Editthis wikifarm
            # It has a page view limit
            # Gamepedia wikifarm
            # ['http://dawngate.gamepedia.com/index.php', 'http://dawngate.gamepedia.com/api.php', u'Spell Vanquish.png'],
            # Neoseeker wikifarm
            # ['http://digimon.neoseeker.com/w/index.php', 'http://digimon.neoseeker.com/w/api.php', u'Ogremon card.png'],
            # Orain wikifarm
            # ['http://mc.orain.org/w/index.php', 'http://mc.orain.org/w/api.php', u'Mojang logo.svg'],
            # Referata wikifarm
            # ['http://wikipapers.referata.com/w/index.php', 'http://wikipapers.referata.com/w/api.php', u'Avbot logo.png'],
            # ShoutWiki wikifarm
            # ['http://commandos.shoutwiki.com/w/index.php', 'http://commandos.shoutwiki.com/w/api.php', u'Night of the Wolves loading.png'],
            # Wiki-site wikifarm
            # ['http://minlingo.wiki-site.com/index.php', 'http://minlingo.wiki-site.com/api.php', u'一 (書方灋ᅗᅩ).png'],
            # Wikkii wikifarm
            # It seems offline
        ]

        requests.Session().headers = {"User-Agent": str(UserAgent())}
        for index, api, filetocheck in tests:
            # Testing with API
            print("\nTesting", api)
            config_for_api_php = {
                "api": api,
                "delay": 0,
                "retries": 5,
                "date": "20150807",
            }
            config_for_api_php["path"] = tempfile.mkdtemp()
            with requests.get(
                api + "?action=query&meta=siteinfo&siprop=statistics&format=json",
                headers={"User-Agent": str(UserAgent())},
            ) as get_response:
                image_count = int(get_response.json()["query"]["statistics"]["images"])

            print("Trying to parse", filetocheck, "with API")
            image_dumper_from_api = ImageDumper(config_for_api_php)
            image_dumper_from_api.fetchTitles()
            for image_info in image_dumper_from_api.image_info_list:
                print(str(image_info))
            self.assertEqual(len(image_dumper_from_api.image_info_list), image_count)
            self.assertTrue(
                filetocheck
                in [
                    filename
                    for filename, url, uploader in image_dumper_from_api.image_info_list
                ]
            )

            # Testing with index
            print("\nTesting", index)
            config_for_index_php = {
                "index": index,
                "delay": 0,
                "retries": 5,
                "date": "20150807",
            }
            config_for_api_php["path"] = tempfile.mkdtemp()
            with requests.get(
                api + "?action=query&meta=siteinfo&siprop=statistics&format=json",
                headers={"User-Agent": str(UserAgent())},
            ) as get_response:
                image_count = int(get_response.json()["query"]["statistics"]["images"])

            print("Trying to parse", filetocheck, "with index")
            image_dumper_from_index = ImageDumper(config_for_index_php)
            image_dumper_from_index.fetchTitles()
            # print(111,
            #     set([filename for filename, url, uploader in result_api])
            #     - set([filename for filename, url, uploader in image_dumper_from_index.image_info_list])
            # )
            # print("test: ")
            # for test in tests:
            #     print(test)
            # print("image_dumper_from_index.image_info_list: " + image_dumper_from_index.image_info_list)
            # print("len(image_dumper_from_index.image_info_list): " + len(result_image_dumper_from_index.image_info_listindex))
            # print("image_count: " + image_count)
            self.assertEqual(len(image_dumper_from_index.image_info_list), image_count)
            self.assertTrue(
                filetocheck
                in [
                    filename
                    for filename, url, uploader in image_dumper_from_index.image_info_list
                ]
            )

            # Compare every image in both lists, with/without API
            count = 0
            for image_info in image_dumper_from_api.image_info_list:
                self.assertEqual(
                    image_info.filename(),
                    image_dumper_from_index.image_info_list[count].filename(),
                    f"{image_info.filename()} and {image_dumper_from_index.image_info_list[count].filename()} are different",
                )
                self.assertEqual(
                    image_info.url(),
                    image_dumper_from_index.image_info_list[count].url(),
                    f"{image_info.url()} and {image_dumper_from_index.image_info_list[count].url()} are different",
                )
                self.assertEqual(
                    image_info.uploader,
                    image_dumper_from_index.image_info_list[count].uploader,
                    f"{image_info.uploader} and {image_dumper_from_index.image_info_list[count].uploader} are different",
                )
                count += 1

    def test_getPageTitles(self):
        """This test download the title list using API and index.php
        Compare both lists in length and title by title
        Check the presence of some special titles, like odd chars
        The tested wikis are from different wikifarms and some alone"""

        print("\n", "#" * 73, "\n", "test_getPageTitles", "\n", "#" * 73)
        tests = [
            # Alone wikis
            # Test fails on ArchiveTeam
            # with pagetocheck not in result_index
            # [
            #     "https://wiki.archiveteam.org/index.php",
            #     "https://wiki.archiveteam.org/api.php",
            #     u"April Fools' Day",
            # ],
            [
                "https://riverdale.fandom.com/index.php",
                "https://riverdale.fandom.com/api.php",
                "Chilling Adventures of Sabrina",
            ],
            # [
            #     "http://skilledtests.com/wiki/index.php",
            #     "http://skilledtests.com/wiki/api.php",
            #     u"Conway's Game of Life",
            # ],
            # Test old allpages API behaviour
            # [
            #     'http://wiki.damirsystems.com/index.php',
            #     'http://wiki.damirsystems.com/api.php',
            #     'SQL Server Tips'
            # ],
            # Test BOM encoding
            # [
            #     'http://www.libreidea.org/w/index.php',
            #     'http://www.libreidea.org/w/api.php',
            #     'Main Page'
            # ],
        ]

        requests.Session().headers = {"User-Agent": str(UserAgent())}
        for index, api, pagetocheck in tests:
            # Testing with API
            print("\nTesting", api)
            print("Trying to parse", pagetocheck, "with API")
            config_for_api_php = {
                "api": api,
                "index": "",
                "delay": 0,
                "namespaces": ["all"],
                "exnamespaces": [],
                "date": datetime.datetime.now().strftime("%Y%m%d"),
                "path": ".",
                "retries": 5,
            }

            title_list_filename = fetchPageTitles(config_for_api_php)
            with open(title_list_filename) as titles_api_file:
                result_api = titles_api_file.read().splitlines()
                os.remove(title_list_filename)
                # print(result_api)
                self.assertTrue(pagetocheck in result_api)

                # Testing with index
                print("Testing", index)
                print("Trying to parse", pagetocheck, "with index")
                config_for_index_php = {
                    "index": index,
                    "api": "",
                    "delay": 0,
                    "namespaces": ["all"],
                    "exnamespaces": [],
                    "date": datetime.datetime.now().strftime("%Y%m%d"),
                    "path": ".",
                    "retries": 5,
                }

                titles_index = fetchPageTitles(config=config_for_index_php)
                with open(titles_index) as titles_index_file:
                    result_index = titles_index_file.read().splitlines()
                    # os.remove(titles_index)
                    # print("result_index: ")
                    # for result in result_index:
                    #     print(result)
                    self.assertTrue(pagetocheck in result_index)
                    print(len(result_api))
                    print(len(result_index))
                    self.assertEqual(len(result_api), len(result_index))

                    # Compare every page in both lists, with/without API
                    count = 0
                    for pagename_api in result_api:
                        chk = pagename_api in result_index
                        self.assertEqual(
                            chk, True, "%s not in result_index" % (pagename_api)
                        )
                        count += 1

        requests.Session().close()

    def test_getWikiEngine(self):
        print("\n", "#" * 73, "\n", "test_getWikiEngine", "\n", "#" * 73)
        tests = [
            ["https://www.dokuwiki.org", "DokuWiki"],
            # ['http://wiki.openwrt.org', 'DokuWiki'],
            # ['http://skilledtests.com/wiki/', 'MediaWiki'],
            # ['http://moinmo.in', 'MoinMoin'],
            ["https://wiki.debian.org", "MoinMoin"],
            ["http://twiki.org/cgi-bin/view/", "TWiki"],
            # ['http://nuclearinfo.net/Nuclearpower/CurrentReactors', 'TWiki'],
            ["http://www.pmwiki.org/", "PmWiki"],
            ["http://www.apfelwiki.de/", "PmWiki"],
            ["http://wiki.wlug.org.nz/", "PhpWiki"],
            # ['http://wiki.greenmuseum.org/', 'PhpWiki'],
            # ['http://www.cmswiki.com/tiki-index.php', 'TikiWiki'],
            ["http://www.wasteflake.com/", "TikiWiki"],
            ["http://foswiki.org/", "FosWiki"],
            ["http://www.w3c.br/Home/WebHome", "FosWiki"],
            # ['http://mojomojo.org/', 'MojoMojo'],
            # ['http://wiki.catalystframework.org/wiki/', 'MojoMojo'],
            # ['https://www.ictu.nl/archief/wiki.noiv.nl/xwiki/bin/view/Main', 'XWiki'],
            # ['https://web.archive.org/web/20080517021020id_/http://berlin.xwiki.com/xwiki/bin/view/Main/WebHome', 'XWiki'],
            ["http://www.xwiki.org/xwiki/bin/view/Main/WebHome", "XWiki"],
            # ['https://confluence.atlassian.com/', 'Confluence'],
            # ['https://wiki.hybris.com/dashboard.action', 'Confluence'],
            ["https://confluence.sakaiproject.org/", "Confluence"],
            # ['http://demo.bananadance.org/', 'Banana Dance'],
            # ["http://wagn.org/", "Wagn"],
            # ['http://wiki.ace-mod.net/', 'Wagn'],
            # ['https://success.mindtouch.com/', 'MindTouch'],
            # ['https://jspwiki.apache.org/', 'JSPWiki'],
            # ['http://www.ihear.com/FreeCLAS/', 'JSPWiki'],
            ["http://www.wikkawiki.org/HomePage", "WikkaWiki"],
            # ['http://puppylinux.org/wikka/', 'WikkaWiki'],
            ["https://www.cybersphere.net/", "MediaWiki"],
            # ['http://web.archive.org/web/20060717202033id_/http://www.comawiki.org/CoMa.php?CoMa=startseite', 'CoMaWiki'],
            ["http://bootbook.de/CoMa.php", "CoMaWiki"],
            # ['http://wikini.net/wakka.php', 'WikiNi'],
            ["http://wiki.raydium.org/wiki/", "WikiNi"],
            # ['http://wiki.cs.cityu.edu.hk/CitiWiki/SourceCode', 'CitiWiki'],
            # ['http://wackowiki.sourceforge.net/test/', 'WackoWiki'],
            ["http://www.sw4me.com/wiki/", "WackoWiki"],
            # ['http://lslwiki.net/lslwiki/wakka.php', 'WakkaWiki'],
            # ["http://kw.pm.org/wiki/index.cgi", "Kwiki"],
            ["http://wiki.wubi.org/index.cgi", "Kwiki"],
            # ['http://perl.bristolbath.org/index.cgi', 'Kwiki'],
            # ['http://www.anwiki.com/', 'Anwiki'],
            # ['http://www.anw.fr/', 'Anwiki'],
            ["http://www.aneuch.org/", "Aneuch"],
            ["http://doc.myunixhost.com/", "Aneuch"],
            ["http://www.bitweaver.org/wiki/index.php", "bitweaver"],
            # ['http://wiki.e-shell.org/Home', 'Zwiki'],
            # ["http://leo.zwiki.org/", "Zwiki"],
            # ['http://accessibility4all.wikispaces.com/', 'Wikispaces'],
            ["http://darksouls.wikidot.com/", "Wikidot"],
            # ["http://www.wikifoundrycentral.com/", "Wetpaint"],
            ["http://wiki.openid.net/", "PBworks"],
        ]
        for wiki, engine in tests:
            print("Testing", wiki)
            try:
                guess_engine = getWikiEngine(wiki)
            except ConnectionError:
                print("%s failed to load, skipping..." % (wiki))
                continue
            print(f"Got: {guess_engine}, expected: {engine}")
            self.assertEqual(guess_engine, engine)

    def test_mwGetAPIAndIndex(self):
        print("\n", "#" * 73, "\n", "test_mwGetAPIAndIndex", "\n", "#" * 73)
        tests = [
            # Alone wikis
            [
                "https://wiki.archiveteam.org",
                "https://wiki.archiveteam.org/api.php",
                "https://wiki.archiveteam.org/index.php",
            ],
            # ['http://skilledtests.com/wiki/', 'http://skilledtests.com/wiki/api.php', 'http://skilledtests.com/wiki/index.php'],
            # Editthis wikifarm
            # It has a page view limit
            # Gamepedia wikifarm
            # ['http://dawngate.gamepedia.com', 'http://dawngate.gamepedia.com/api.php', 'http://dawngate.gamepedia.com/index.php'],
            # Neoseeker wikifarm
            # ['http://digimon.neoseeker.com', 'http://digimon.neoseeker.com/w/api.php', 'http://digimon.neoseeker.com/w/index.php'],
            # Orain wikifarm
            # ['http://mc.orain.org', 'http://mc.orain.org/w/api.php', 'http://mc.orain.org/w/index.php'],
            # Referata wikifarm
            # ['http://wikipapers.referata.com', 'http://wikipapers.referata.com/w/api.php', 'http://wikipapers.referata.com/w/index.php'],
            # ShoutWiki wikifarm
            # ['http://commandos.shoutwiki.com', 'http://commandos.shoutwiki.com/w/api.php', 'http://commandos.shoutwiki.com/w/index.php'],
            # Wiki-site wikifarm
            # ['http://minlingo.wiki-site.com', 'http://minlingo.wiki-site.com/api.php', 'http://minlingo.wiki-site.com/index.php'],
            # Wikkii wikifarm
            # It seems offline
        ]
        for wiki, api, index in tests:
            print("Testing", wiki)
            api_info = ApiInfo(wiki)
            api2 = api_info.api_string
            index2 = api_info.index_php_url
            self.assertEqual(api, api2)
            self.assertEqual(index, index2)


def main():
    TestDumpgenerator().test_delay()
    TestDumpgenerator().test_getImages()
    TestDumpgenerator().test_getPageTitles()
    TestDumpgenerator().test_getWikiEngine()
    TestDumpgenerator().test_mwGetAPIAndIndex()


if __name__ == "__main__":
    main()
