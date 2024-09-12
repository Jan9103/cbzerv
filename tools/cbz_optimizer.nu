#!/usr/bin/env nu

const IMAGE_FILE_EXTENSIONS = [
  "jpeg" "jpg"
  "png"
  # "webp" (webp supports animations, ff does not)
  # "gif" (git supports animations, ff does not)
  # "svg" (conversion would be lossy)
]

# example usage:
#   nu cbz_2ff_optimizer.nu --use-ff --png-tool optipng *.cbz
#   nu cbz_2ff_optimizer.nu --use-ff c1.cbz c2.cbz
def main [
  ...cbz_files: path
  --cbz-threads: int = 1  # optimize multiple **cbz** files at the same time (warning: the commandline output will be a mess)
  --img-threads: int = 1  # optimize multiple **image** files at the same time (warning: the commandline output will be a mess)
  --png-tool: string = "none"  # "none", "optipng" or "pngcrush"
  --use-ff  # convert to .ff.bz2 if its smaller (requires ImageMagick7 and bzip2)
  --no-check-magick  # do not check the imagemagick version (can lead to data-loss)
] {
  # verify ImageMagick version
  if (not $use_ff) or $no_check_magick or (not (^magick --version | str starts-with 'Version: ImageMagick 7')) {
    # image-magick 6 (and older) does not support FF
    # if image-magick encounters a unsupported format it does not complain and instead just outputs something (probably the input?)
    # -> crash here if unsure to avoid data-loss
    error make {msg: "Unable to verify ImageMagick version as 7. use --no-check-magick to skip this check if you know what you are doing."}
  }

  if $cbz_threads < 1 or $img_threads < 1 { print --stderr 'Cant work with < 1 thread.'; return }

  $cbz_files | par-each --threads $cbz_threads {|cbz_file|
    # check if it is potentially compressable
    if (^zipinfo -1 $cbz_file | lines | where (($it | split row '.' | last) in $IMAGE_FILE_EXTENSIONS)) == [] { print $'cant compress ($cbz_file)'; return }
    print $'compressing ($cbz_file)...'

    let cbz_file = ($cbz_file | path expand)
    let tmpdir = (mktemp -d)
    cd $tmpdir
    ^unzip $cbz_file

    if $png_tool != "none" {
      ls --full-paths $tmpdir
      | where type == "file"
      | get name
      | where ($it | split row '.' | last) == "png"
      | par-each --threads $img_threads {|png|
        if $png_tool == "pngcrush" {
          ^pngcrush -l 9 -m 0 -e '.png.crushed' $png
          mv -f $'($png).crushed' $png
        } else {
          ^optipng -o7 $png
        }
      }
    }

    if $use_ff {
      ls --full-paths $tmpdir  # do we skip images in sub-dirs? yes. are sub-dirs supported by cbz? maybe, i cant find proper specs.
      | where type == "file"
      | get name
      | where (($it | split row '.' | last) in $IMAGE_FILE_EXTENSIONS)
      | par-each --threads $img_threads {|image|
        let new_name = (($image | split row '.' | range 0..-2 | str join '.') + ".ff.bz2")
        # convert
        ^magick $image "FF:-" | ^bzip2 -zc9 | save -r $new_name
        # delete bigger version
        if (ls $new_name | get 0.size) < (ls $image | get 0.size) { rm -p $image } else { rm -p $new_name }
      }
    }

    ^zip -r9 tmp.zip *
    mv tmp.zip $cbz_file  # mv instead of override (or rm; zip) to avoid issues on crash
    cd /; rm -prf $tmpdir
  }
}
