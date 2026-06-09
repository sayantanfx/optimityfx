#!/usr/bin/env bash
# OptimityFX blog quick-control. Run from the website/ folder.
#   ./manage.sh list                 # show recent posts (newest first)
#   ./manage.sh unpublish <slug>     # hide from site (keeps the file) -> rebuild + deploy
#   ./manage.sh publish   <slug>     # re-publish a hidden post -> rebuild + deploy
#   ./manage.sh delete    <slug>     # permanently remove the post -> rebuild + deploy
#   ./manage.sh edit      <slug>     # open the post in your editor (then run rebuild)
#   ./manage.sh rebuild              # rebuild + deploy after a manual edit
set -e
cd "$(dirname "$0")"
DIR="content/blog"

find_file() { ls $DIR/*-"$1".md 2>/dev/null || ls $DIR/*"$1"*.md 2>/dev/null | head -1; }

deploy() {
  python3 build.py >/dev/null
  git add -A && git commit -q -m "blog: $1" && git push origin main
  echo "✅ Deployed. Live in ~60s: https://www.optimityfx.com/blog-$2.html"
}

case "$1" in
  list)
    echo "Recent posts (newest first):"
    for f in $(ls -r $DIR/*.md 2>/dev/null | grep -v README); do
      slug=$(grep -m1 '^slug:' "$f" | sed 's/slug:[[:space:]]*//')
      status=$(grep -m1 '^status:' "$f" | sed 's/status:[[:space:]]*//'); status=${status:-published}
      title=$(grep -m1 '^title:' "$f" | sed 's/title:[[:space:]]*//')
      printf "  [%-9s] %-40s %s\n" "$status" "$slug" "$title"
    done ;;
  unpublish)
    f=$(find_file "$2"); [ -z "$f" ] && { echo "Post not found: $2"; exit 1; }
    sed -i '' 's/^status:.*/status: draft/' "$f" 2>/dev/null || sed -i 's/^status:.*/status: draft/' "$f"
    grep -q '^status:' "$f" || printf '\n' # noop
    deploy "unpublish $2" "$2" ;;
  publish)
    f=$(find_file "$2"); [ -z "$f" ] && { echo "Post not found: $2"; exit 1; }
    sed -i '' 's/^status:.*/status: published/' "$f" 2>/dev/null || sed -i 's/^status:.*/status: published/' "$f"
    deploy "publish $2" "$2" ;;
  delete)
    f=$(find_file "$2"); [ -z "$f" ] && { echo "Post not found: $2"; exit 1; }
    rm -f "$f"; rm -f "blog-$2.html"
    deploy "delete $2" "$2" ;;
  edit)
    f=$(find_file "$2"); [ -z "$f" ] && { echo "Post not found: $2"; exit 1; }
    "${EDITOR:-open}" "$f"; echo "After editing, run: ./manage.sh rebuild" ;;
  rebuild)
    deploy "manual rebuild" "" ;;
  *)
    echo "Usage: ./manage.sh {list|unpublish <slug>|publish <slug>|delete <slug>|edit <slug>|rebuild}" ;;
esac
