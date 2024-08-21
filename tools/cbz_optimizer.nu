#!/usr/bin/env nu

# optimize cbz files by optimizing the compression of the contained .png files
def main [
  ...cbz_files: path
  --threads: int = 1  # optimize multiple cbz files at the same time (warning: the commandline output will be a mess)
  --tool: string = "optipng"  # either "optipng" or "pngcrush"
] {
  if not ($tool in ["optipng", "pngcrush"]) { print --stderr $'Unknown compression tool: ($tool). see "--help" for a list of supported tools.'; return }
  if $threads < 1 { print --stderr 'Cant work with < 1 thread.'; return }
  $cbz_files | par-each --threads $threads {|cbz_file|
    let cbz_file = ($cbz_file | path expand)
    let tmpdir = (mktemp -d)
    let pngs = (^zipinfo -1 $cbz_file | lines | where ($it | str ends-with '.png'))
    if ($pngs | length) == 0 {
      return
    }
    ^unzip -d $tmpdir $cbz_file ...$pngs
    cd $tmpdir
    ls --full-paths $tmpdir
    | get name
    | each {|png|
      if $tool == "pngcrush" {
        ^pngcrush -l 9 -m 0 -e '.png.crushed' $png
        mv -f $'($png).crushed' $png
      } else {
        ^optipng -o7 $png
      }
      ^zip -u9 $cbz_file ($png | path relative-to $tmpdir)
      rm $png
    }
    rm -r $tmpdir
  }
}
