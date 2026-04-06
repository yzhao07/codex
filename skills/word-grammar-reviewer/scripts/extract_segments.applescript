on run argv
  set outputPath to item 1 of argv
  set outputFile to POSIX file outputPath
  tell application "Microsoft Word"
    activate
    set mydoc to open file name outputFile
    set pList to every paragraph of text object of mydoc
    set outLines to {}
    repeat with i from 1 to count of pList
      set pRef to item i of pList
      set r to text object of pRef
      set startPos to start of content of r
      set rawText to content of r
      set end of outLines to (i as text) & tab & (startPos as text) & tab & rawText
    end repeat
    close mydoc saving no
    set AppleScript's text item delimiters to linefeed
    return outLines as text
  end tell
end run
