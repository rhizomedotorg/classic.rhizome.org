#!/bin/bash

# @author: Radek Kavan
# @e-mail: jooke@centrum.cz
# @web: http://internet.billboard.cz/ http://gnu.linux-sysadmin.org


########### PATHS #############
CACHE_DIR=/var/cache/nginx/django
GREP=/bin/grep
TMP_FILE=/tmp/cdnIvalidation
###############################


die () {
    cecho "\c " $black
    cecho "$@" $red
    exit 1
}


checkStatus () {
if [ "$?" -ne 0 ]; then
    die "$@"
fi

}


testDirs () {
    [ ! -d "$CACHE_DIR" ] && die "Your proxy_cache_path (\"${CACHE_DIR}\") is wrong,\
    \nedit please this script and set correctly CACHE_DIR variable."
    > "$TMP_FILE"
}

function cecho ()
{
export black='\E[0m\c'
export boldblack='\E[1;0m\c'
export red='\E[31m\c'
export boldred='\E[1;31m\c'
export green='\E[32m\c'
export boldgreen='\E[1;32m\c'
export yellow='\E[33m\c'
export boldyellow='\E[1;33m\c'
export blue='\E[34m\c'
export boldblue='\E[1;34m\c'
export magenta='\E[35m\c'
export boldmagenta='\E[1;35m\c'
export cyan='\E[36m\c'
export boldcyan='\E[1;36m\c'
export white='\E[37m\c'
export boldwhite='\E[1;37m\c'
local default_msg="No message passed."
message=${1:-$default_msg}
color=${2:-$black}

  echo -e "$color"
  echo -ne "$message"
  tput sgr0
  echo -e "$black"
  return
}


inputProxyCachePattern () {
                        cecho "\c " $black
                        cecho "Enter pattern of your file which you want to purge: " $boldblue
                        read proxyKey
                        checkStatus "Something is wrong with your pattern"
                        if [ -z "$proxyKey" ]; then die "Do you insert any pattern?"; fi
}

findPatterInFile () {
                     filesWithPattern=$(grep -Ri "$proxyKey" "$CACHE_DIR"/* | awk '{print $3}')
                     for file in $filesWithPattern
                         do
                             grep -Hai "$proxyKey" "$file" | grep KEY >> "$TMP_FILE"
                             checkStatus "I can't find your pattern in you cache: $proxyKey in file: $file"
                     done


}

showFoundedKeys () {
                    KEY_NUMBER=1
                    cecho "\c " $black
                    cecho "I found follows keys:\n" $cyan
                    cat "$TMP_FILE" | while read Keys
                                        do
                                            echo "$KEY_NUMBER: `echo $Keys | awk '{print $2}'`"
                                            KEY_NUMBER=$(($KEY_NUMBER + 1))
                                        done


}

deleteProxyCacheKey () {
                        cecho "\c " $black
                        cecho "Enter number of item which you want to purge.: " $boldblue
                        read itemNumber
                        FILE=$(sed -n "${itemNumber}p" /tmp/cdnIvalidation | awk 'BEGIN { FS = ":"} ; {print $1}')
                        KEY=$(sed -n "${itemNumber}p" /tmp/cdnIvalidation | awk 'BEGIN { FS = ":"} ; {print $3}')
                        cecho "Are you sure you want to delete?: $KEY (y/n): " $yellow
                        read invalideKey
                        if [ "$invalideKey" != "y" ]
                            then
                                die "Operation has been cancelled."
                                exit 0
                        else
                            rm -f "$FILE"
                            checkStatus "Error: i can't remove this file: $FILE"
                            cecho "Success\n" $boldyellow
                        fi

}

### MAIN ###
testDirs
inputProxyCachePattern
findPatterInFile
showFoundedKeys
deleteProxyCacheKey
exit 0
