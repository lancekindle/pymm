<map version="freeplane 1.3.0">
<!--To view this file, download free mind mapping software Freeplane from http://freeplane.sourceforge.net -->
<attribute_registry SHOW_ATTRIBUTES="selected"/>
<node ID="ID_1723255651" CREATED="1283093380553" MODIFIED="1453697180839"><richcontent TYPE="NODE">

<html>
  <head>
    
  </head>
  <body>
    <p>
      Root Node, <b>Bold Node!&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;haha! </b>
    </p>
    <table border="0" style="border-top-style: solid; border-right-style: solid; border-bottom-style: solid; border-left-style: solid; border-left-width: 0; border-bottom-width: 0; width: 80%; border-right-width: 0; border-top-width: 0">
      <tr>
        <td valign="top" style="border-top-style: solid; border-right-style: solid; border-bottom-style: solid; border-left-style: solid; border-bottom-width: 1; border-left-width: 1; width: 33%; border-right-width: 1; border-top-width: 1">
          <p style="margin-left: 1; margin-bottom: 1; margin-top: 1; margin-right: 1">
            
          </p>
        </td>
        <td valign="top" style="border-top-style: solid; border-right-style: solid; border-bottom-style: solid; border-left-style: solid; border-bottom-width: 1; border-left-width: 1; width: 33%; border-right-width: 1; border-top-width: 1">
          <p style="margin-left: 1; margin-bottom: 1; margin-top: 1; margin-right: 1">
            
          </p>
        </td>
        <td valign="top" style="border-top-style: solid; border-right-style: solid; border-bottom-style: solid; border-left-style: solid; border-bottom-width: 1; border-left-width: 1; width: 33%; border-right-width: 1; border-top-width: 1">
          <p style="margin-left: 1; margin-bottom: 1; margin-top: 1; margin-right: 1">
            
          </p>
        </td>
      </tr>
    </table>
    <p>
      <b>jdjdjdfjfjf ooooh yeah</b>
    </p>
  </body>
</html>

</richcontent>
<hook NAME="MapStyle" zoom="1.1">
    <properties show_icon_for_attributes="false" show_note_icons="true" show_notes_in_map="true"/>

<map_styles>
<stylenode LOCALIZED_TEXT="styles.root_node">
<stylenode LOCALIZED_TEXT="styles.predefined" POSITION="right">
<stylenode LOCALIZED_TEXT="default" MAX_WIDTH="600" COLOR="#000000" STYLE="as_parent">
<font NAME="SansSerif" SIZE="10" BOLD="false" ITALIC="false"/>
</stylenode>
<stylenode LOCALIZED_TEXT="defaultstyle.details"/>
<stylenode LOCALIZED_TEXT="defaultstyle.note"/>
<stylenode LOCALIZED_TEXT="defaultstyle.floating">
<edge STYLE="hide_edge"/>
<cloud COLOR="#f0f0f0" SHAPE="ROUND_RECT"/>
</stylenode>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.user-defined" POSITION="right">
<stylenode LOCALIZED_TEXT="styles.topic" COLOR="#18898b" STYLE="fork">
<font NAME="Liberation Sans" SIZE="10" BOLD="true"/>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.subtopic" COLOR="#cc3300" STYLE="fork">
<font NAME="Liberation Sans" SIZE="10" BOLD="true"/>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.subsubtopic" COLOR="#669900">
<font NAME="Liberation Sans" SIZE="10" BOLD="true"/>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.important">
<icon BUILTIN="yes"/>
</stylenode>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.AutomaticLayout" POSITION="right">
<stylenode LOCALIZED_TEXT="AutomaticLayout.level.root" COLOR="#000000">
<font SIZE="18"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,1" COLOR="#0033ff">
<font SIZE="16"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,2" COLOR="#00b439">
<font SIZE="14"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,3" COLOR="#990000">
<font SIZE="12"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,4" COLOR="#111111">
<font SIZE="10"/>
</stylenode>
</stylenode>
</stylenode>
</map_styles>
</hook>
<hook NAME="AutomaticEdgeColor" COUNTER="2"/>
<hook NAME="accessories/plugins/HierarchicalIcons2.properties"/>
<richcontent TYPE="NOTE">

<html>
  <head>
    
  </head>
  <body>
    <p>
      this is a note
    </p>
  </body>
</html>
</richcontent>
<attribute NAME="blah" VALUE="2" OBJECT="org.freeplane.features.format.FormattedNumber|2"/>
<node TEXT="Child Node 1" POSITION="right" ID="ID_1707799934" CREATED="1421458652275" MODIFIED="1423120002131"><richcontent TYPE="NOTE">

<html>
  <head>
    
  </head>
  <body>
    <p>
      1st child note
    </p>
  </body>
</html>
</richcontent>
<node TEXT="Subchild 1 w/ arc cloud" ID="ID_1244434831" CREATED="1421458663887" MODIFIED="1421461041155">
<cloud COLOR="#3333ff" SHAPE="ARC"/>
<node TEXT="sub-subchild w/ star cloud" ID="ID_1458322322" CREATED="1421458700021" MODIFIED="1421461002737">
<cloud COLOR="#cc00cc" SHAPE="STAR"/>
</node>
<node TEXT="subsub w/ rect cloud" ID="ID_404658972" CREATED="1421460955591" MODIFIED="1421460978871">
<cloud COLOR="#ff3333" SHAPE="RECT"/>
</node>
<node TEXT="subsub w/ round rect cloud" ID="ID_1441499441" CREATED="1421461004484" MODIFIED="1421461027812">
<cloud COLOR="#66ff66" SHAPE="ROUND_RECT"/>
</node>
</node>
</node>
<node TEXT="Child Node 2" POSITION="right" ID="ID_612656001" CREATED="1421460933821" MODIFIED="1422988552060" COLOR="#ff9933" STYLE="bubble" MAX_WIDTH="30" MIN_WIDTH="20">
<edge COLOR="#7c007c"/>
<node TEXT="1" OBJECT="java.lang.Long|1" ID="ID_128388905" CREATED="1422987573354" MODIFIED="1422987580660"/>
<node TEXT="2" OBJECT="java.lang.Long|2" ID="ID_210612684" CREATED="1422987576717" MODIFIED="1422987582132"/>
</node>
<node TEXT="Child Node 3 w/ colored edge and thick line and horizontal style" POSITION="right" ID="ID_721787619" CREATED="1421461049972" MODIFIED="1421461123315">
<edge STYLE="horizontal" COLOR="#3333ff" WIDTH="4"/>
</node>
<node TEXT="a summary node" POSITION="right" ID="ID_233410359" CREATED="1422119552579" MODIFIED="1453695125062">
<edge COLOR="#ff0000"/>
<attribute NAME="blank text" VALUE="this has blank text"/>
<hook NAME="SummaryNode"/>
</node>
<node TEXT="" POSITION="left" ID="ID_24706037" CREATED="1422912661004" MODIFIED="1422912672207">
<edge STYLE="linear" COLOR="#ff0000"/>
</node>
<node TEXT="cojoined node1" POSITION="left" ID="ID_69893373" CREATED="1422912663523" MODIFIED="1453697034298">
<edge STYLE="bezier" COLOR="#ff0000"/>
<arrowlink SHAPE="CUBIC_CURVE" COLOR="#000000" WIDTH="2" TRANSPARENCY="80" FONT_SIZE="9" FONT_FAMILY="SansSerif" DESTINATION="ID_818221677" STARTINCLINATION="40;0;" ENDINCLINATION="40;0;" STARTARROW="NONE" ENDARROW="DEFAULT"/>
</node>
<node TEXT="cojoined node2" POSITION="left" ID="ID_818221677" CREATED="1422912664392" MODIFIED="1453695231184">
<edge STYLE="sharp_linear" COLOR="#00ff00"/>
</node>
<node POSITION="left" ID="ID_1388445466" CREATED="1422912665061" MODIFIED="1422988979210"><richcontent TYPE="NODE">

<html>
  <head>
    
  </head>
  <body>
    <p>
      yayayayaya<b>&#160;this is awesome!</b>
    </p>
  </body>
</html>
</richcontent>
<edge STYLE="sharp_bezier" COLOR="#ff00ff"/>
</node>
<node TEXT="some cooler edges here" POSITION="left" ID="ID_1466334443" CREATED="1422912665737" MODIFIED="1453697153933">
<edge STYLE="horizontal" COLOR="#00ffff"/>
</node>
<node TEXT="&amp; floats" POSITION="left" ID="ID_1965736443" CREATED="1422912666979" MODIFIED="1422914604780">
<edge STYLE="hide_edge" COLOR="#ffff00"/>
</node>
<node TEXT="this one links to root" POSITION="left" ID="ID_438584984" CREATED="1453697157261" MODIFIED="1453697176682" LINK="#ID_1723255651">
<edge COLOR="#0000ff"/>
</node>
</node>
</map>
