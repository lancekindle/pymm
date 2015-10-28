<map version="freeplane 1.3.0">
<!--To view this file, download free mind mapping software Freeplane from http://freeplane.sourceforge.net -->
<node TEXT="Root Node" ID="ID_1723255651" CREATED="1283093380553" MODIFIED="1422988948511"><hook NAME="MapStyle" zoom="1.1">
    <properties show_icon_for_attributes="true"/>

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
<hook NAME="AutomaticEdgeColor" COUNTER="12"/>
<hook NAME="accessories/plugins/HierarchicalIcons2.properties"/>
<node TEXT="Child Node 1" POSITION="right" ID="ID_1707799934" CREATED="1421458652275" MODIFIED="1422651305952">
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
<node TEXT="" POSITION="right" ID="ID_233410359" CREATED="1422119552579" MODIFIED="1422651309693">
<edge COLOR="#ff0000"/>
<attribute NAME="blank text" VALUE="this has blank text"/>
<hook NAME="SummaryNode"/>
</node>
<node TEXT="" POSITION="left" ID="ID_24706037" CREATED="1422912661004" MODIFIED="1422912672207">
<edge STYLE="linear" COLOR="#ff0000"/>
</node>
<node TEXT="" POSITION="left" ID="ID_69893373" CREATED="1422912663523" MODIFIED="1422912677375">
<edge STYLE="bezier" COLOR="#0000ff"/>
</node>
<node TEXT="" POSITION="left" ID="ID_818221677" CREATED="1422912664392" MODIFIED="1422912682543">
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
<node TEXT="" POSITION="left" ID="ID_1466334443" CREATED="1422912665737" MODIFIED="1422988948507">
<edge STYLE="horizontal" COLOR="#00ffff"/>
</node>
<node TEXT="&amp; floats" POSITION="left" ID="ID_1965736443" CREATED="1422912666979" MODIFIED="1422914604780">
<edge STYLE="hide_edge" COLOR="#ffff00"/>
</node>
</node>
</map>
