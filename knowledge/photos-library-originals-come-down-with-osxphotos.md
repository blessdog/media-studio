---
id: photos-library-originals-come-down-with-osxphotos
kind: procedure
conflict-key: how-to-get-a-photos-library-video-into-the-studio
status: live
supersedes: []
verified-on: 2026-09-09
applies-when: Ryan drags photos or videos from the Photos app into the chat, or names assets in a .photoslibrary; the paths that arrive are resources/derivatives/... JPEGs, and a _4_5005_c.jpeg is the poster frame of a VIDEO
not-when: files already on disk under /Users/SSDrive/Movies or a workspace media/ folder; those are intake.file_media, no Photos step
route: query database/Photos.sqlite (ZASSET by ZUUID for ZKIND, ZDURATION, ZFILENAME), then ~/.local/bin/osxphotos export <dir> --library <lib> --uuid <UUID>... --download-missing --use-photokit --skip-edited --skip-live
sibling: none
asked-as:
  - the images Ryan dragged in are jpegs but the clips are videos
  - how do I get the original video out of the Photos library
  - originals folder in the photoslibrary is empty
  - export iCloud photos from the command line
---

**A file dragged from Photos into the chat is a derivative JPEG, and the
originals folder can be empty because the library is iCloud-optimised.
The route is osxphotos with `--download-missing`, not a hand-rolled copy.**

Measured 2026-09-09 on `/Users/SSDrive/Pictures/Archive/Photos Library.photoslibrary`:
ten dragged "images" were ten `.mov` assets (ZKIND=1, 5 to 114 s), the
`originals/` tree held zero files, and every video resource in
ZINTERNALRESOURCE had ZLOCALAVAILABILITY = -1. `osxphotos export ...
--download-missing --use-photokit` pulled all ten (390 MB) in 25 s.

The one gate: the terminal app needs Photos access. The first run raised a
system dialog and failed; after Ryan clicked Allow, `kTCCServicePhotos` for
`com.mitchellh.ghostty` read 2 in the user TCC database and the second run
succeeded. Check the database, not the settings pane, exactly as the
Full Disk Access rule in AGENTS.md says.

Downstream: `jobs/summer-reel/build.py` conforms the exported clips (portrait
scale, landscape blurred-fill, loudnorm) before they enter a Story IR.
Related: [[the-native-resolve-mcp-server-works-over-stdio]].
