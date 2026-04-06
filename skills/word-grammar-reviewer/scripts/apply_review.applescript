use framework "Foundation"
use scripting additions

on json_string_to_records(jsonText)
  set textObj to current application's NSString's stringWithString:jsonText
  set jsonData to textObj's dataUsingEncoding:(current application's NSUTF8StringEncoding)
  set parsed to current application's NSJSONSerialization's JSONObjectWithData:jsonData options:0 |error|:(missing value)
  return parsed as record
end json_string_to_records

on run argv
  set docPath to item 1 of argv
  set payload to my json_string_to_records(item 2 of argv)
  set targetName to do shell script "basename " & quoted form of docPath
  set commentItems to comments of payload
  set editItems to edits of payload
  set docFile to POSIX file docPath

  tell application "Microsoft Word"
    activate
    try
      close (every document whose name is targetName) saving yes
    end try
    set docRef to open file name docFile
    set track revisions of docRef to true
    set show revisions of docRef to true
    try
      set v to view of active window
      set show comments of v to true
      set show revisions and comments of v to true
      set show insertions and deletions of v to true
    end try

    set sel to selection

    repeat with commentItem in commentItems
      set selection start of sel to (abs_start of commentItem)
      set selection end of sel to (abs_end of commentItem)
      make new Word comment at end of selection with properties {comment text:(comment_text of commentItem)}
    end repeat

    repeat with editItem in editItems
      set selection start of sel to (abs_start of editItem)
      set selection end of sel to (abs_end of editItem)
      set content of sel to (replacement_text of editItem)
    end repeat

    save docRef
    close docRef saving yes
  end tell
end run
