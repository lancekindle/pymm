<map version="freeplane 1.3.0">
<!--To view this file, download free mind mapping software Freeplane from http://freeplane.sourceforge.net -->
<node TEXT="Understanding Node Factories" ID="ID_1723255651" CREATED="1283093380553" MODIFIED="1423250806205" MAX_WIDTH="500" MIN_WIDTH="1"><hook NAME="MapStyle">
    <properties show_icon_for_attributes="true" show_note_icons="true"/>

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
<hook NAME="AutomaticEdgeColor" COUNTER="8"/>
<node TEXT="Terminology" POSITION="right" ID="ID_629662081" CREATED="1423251307062" MODIFIED="1423251310402">
<edge COLOR="#ffff00"/>
<node TEXT="etree element:&#xa;This refers to an element from the ElementTree xml API library" ID="ID_799646004" CREATED="1423251311711" MODIFIED="1423251359364"/>
<node TEXT="ET:&#xa;this also refers to an etree element" ID="ID_1855071553" CREATED="1423251417908" MODIFIED="1423251430881"/>
<node TEXT="ET child:&#xa;this also refers to an element from the ElementTree xml library.&#xa;but &quot;child&quot; implies that it belongs as a subelement to another element." ID="ID_973935764" CREATED="1423251360032" MODIFIED="1423251414332"/>
</node>
<node TEXT="explaination" POSITION="right" ID="ID_747326417" CREATED="1423250467364" MODIFIED="1423250806211" MAX_WIDTH="500" MIN_WIDTH="1">
<edge COLOR="#ff0000"/>
<node TEXT="Each node factory really has 2 functions that are called when a particular node is converted / reverted. The first function called does the main conversion/reversion, adds unconverted / unreverted children to the new element, etc....&#xa;&#xa;the 2nd function (the additional_*) is generally reserved for last minute things done when you have more information on the tree structure. For example, in additional_reversion, we set an elements text and tail (to set readable spacing between elements) depending on if the element has children or not.&#xa;Note that if you add children to the element in this call, they will also be called with additional_reversion(). But if you add children to the parent, those will NOT have additional_reversion() called on them." ID="ID_546032172" CREATED="1423250506277" MODIFIED="1423256325268" MAX_WIDTH="500" MIN_WIDTH="1"/>
<node TEXT="In either of the two functions, if you wish to remove the element / node from the tree, do not use a roundabout method by manipulating element.parent. Instead raise the exception: RemoveElementFromTree, which will cause the MindMapTreeConverter to remove the element from its parent and remove that element and its children from the tree as well. If you choose to simply run parent.remove(element), then this elements children will be converted but will not be part of the final tree. You can use that to your advantage if you have additional configuration done by child elements.&#xa;&#xa;this could be useful, for example, in RichContents case, to add itself to a variable within a node, and then remove itself from the normal tree structure.&#xa;&#xa;When manipulating the parent, make sure to check if parent is not None first. In general, parent should be None IFF the node is the first element (usually the map)" ID="ID_1339943849" CREATED="1423251770441" MODIFIED="1423254836357"/>
</node>
<node TEXT="convert_from_etree_element" POSITION="right" ID="ID_77914619" CREATED="1423250479561" MODIFIED="1423250806233" MAX_WIDTH="500" MIN_WIDTH="1">
<edge COLOR="#0000ff"/>
<node TEXT="1) convert_from_etree_element(element):&#xa;This function is the first conversion part of the element. You will have access to an etree element. Calling super() will create a node out of the element, add all attributes for the node, (e.g. node[&apos;NAME&apos;]), and will also append the elements etree children to the node.&#xa;If you wish to prevent a child etree element from being converted, remove it from the list of children and store it in another variable.&#xa;If you wish to add an etree element to be converted, add it now to the list of children. That child element will then also have the convert_from_etree_element called on it (and the additional_conversion function will be called if applicable)&#xa;In general, though, it is advised to program the child to remove itself from the tree, and attach itself to the parent. This way the parent can set up a default variable which can be overwritten by any present children of the desired type." ID="ID_1481165689" CREATED="1423250581376" MODIFIED="1423254100193" MAX_WIDTH="500" MIN_WIDTH="1"/>
</node>
<node TEXT="additional_conversion" POSITION="right" ID="ID_1970442793" CREATED="1423250488072" MODIFIED="1423250806239" MAX_WIDTH="500" MIN_WIDTH="1">
<edge COLOR="#00ff00"/>
<node TEXT="2) additional_conversion(element):&#xa;this function is called after the entire pymm tree has been set up. Use this function to:&#xa;access / manipulate element.parent&#xa;manipulate the pymm element itself!&#xa;Currently, calling super() has no effect on the element" ID="ID_1902085961" CREATED="1423251590907" MODIFIED="1423252385511"/>
</node>
<node TEXT="revert_to_etree_element" POSITION="right" ID="ID_677248934" CREATED="1423250493443" MODIFIED="1423250806245" MAX_WIDTH="500" MIN_WIDTH="1">
<edge COLOR="#ff00ff"/>
</node>
<node TEXT="additional_reversion" POSITION="right" ID="ID_1932083925" CREATED="1423250499275" MODIFIED="1423250806250" MAX_WIDTH="500" MIN_WIDTH="1">
<edge COLOR="#00ffff"/>
</node>
</node>
</map>
