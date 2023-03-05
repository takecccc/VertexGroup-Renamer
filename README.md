# 概要
変換元の名前と変換先の名前のマッピングリストを用いて、選択されたオブジェクトのVertexGroup名を変換します。

マッピングリストは、Armatureのペアを用いて取得することが可能です。

# 使い方
このフォルダをアドオンとして追加し、VertexGroupRenamerを有効化。

`View 3D > Tool Shelf > Renamer > VertexGroup Renamer`が追加されます。

Armatureのペアからマッピングリストを取得する場合、Armature pairにパラメーターを入力した上で`Get Mapping from Armature`を実行します。

| パラメーター | 内容 |
| --- | --- |
|src|変換元 Armature|
|dst|変換先 Armature|
|max distance|同名のボーンが無い場合にペアを探索する最大距離|

Mapping Pairが設定された状態で、VertexGroup名を変換したいオブジェクトを選択した状態で`Rename VertexGroup`を実行します。
