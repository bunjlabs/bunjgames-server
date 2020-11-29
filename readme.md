# Whirligig game file specification.

Zip archive file with structure:
 - content.xml
 - assets/  - images, audio and video folder

content.xml structure:
~~~
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE game>
<game>
    <items>  <!-- 13 items -->
        <item>
            <number>1</number>  <!-- integer -->
            <name>1</name>  <!-- string -->
            <description>question</description>  <!-- string -->
            <type>standard</type>  <!-- standard, blitz, superblitz -->
            <questions> <!-- 1 for standart, 3 for blitz and superblitz -->
                <question>
                    <description>question</description>  <!-- string -->
                    <text></text>  <!-- string, optional -->
                    <image></image>  <!-- string, optional -->
                    <audio></audio>  <!-- string, optional -->
                    <video></video>  <!-- string, optional -->
                    <answer>
                        <description>answer</description>  <!-- string -->
                        <text></text>  <!-- string, optional -->
                        <image></image>  <!-- string, optional -->
                        <audio></audio>  <!-- string, optional -->
                        <video></video>  <!-- string, optional -->
                    </answer>
                </question>
                ...  <!-- 1 item for standart queston, 3 for blitz and superblitz -->
            </questions>
        </item>
   </items>
   ...
</game>
~~~


# Jeopardy

game packs editor - https://vladimirkhil.com/si/siquester
game packs - https://vladimirkhil.com/si/storage


# ClubChat - in development

https://telegram.me/ClubChatBot?start=clubname