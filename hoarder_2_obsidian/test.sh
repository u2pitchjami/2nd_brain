#!/bin/bash
API_URL="http://192.168.50.12:3000/api/trpc/bookmarks"
TOKEN="Bearer ak1_0754a01fce6afffc9dc2_a83e5717ac99617287ba"
BOOKMARK_ID="k4tzz9wht9h6ghtjh75u3j1c"

DATA='{"0":{"json":null,"meta":{"values":["undefined"]}},"1":{"json":{"text":"food","summary":null}}}'
ENCODED_DATA=$(echo -n "$DATA" | jq -sRr @uri)

curl -X GET "http://192.168.50.12:3000/api/trpc/users.whoami,bookmarks.searchBookmarks?batch=1&input=$ENCODED_DATA" \
-H "Authorization: Bearer ak1_0754a01fce6afffc9dc2_a83e5717ac99617287ba" \
-H "Content-Type: application/json" 

curl -X GET 'https://your-hoarder-instance.com/api/v1/bookmarks?q=your_search_term' \
-H 'Authorization: Bearer YOUR_API_KEY'


#curl -X POST "http://192.168.50.12:3000/api/trpc/bookmarks.summarizeBookmark?batch=1" \
#-H "Authorization: Bearer ak1_0754a01fce6afffc9dc2_a83e5717ac99617287ba" \
#-H "Content-Type: application/json" \
#-d '{"0":{"json":{"bookmarkId":"k4tzz9wht9h6ghtjh75u3j1c"}}}'

#vide le résumé
#curl -X POST "http://192.168.50.12:3000/api/trpc/bookmarks.updateBookmark?batch=1" \
#-H "Authorization: Bearer ak1_0754a01fce6afffc9dc2_a83e5717ac99617287ba" \
#-H "Content-Type: application/json" \
#-d '{"0":{"json":{"bookmarkId":"k4tzz9wht9h6ghtjh75u3j1c","summary":null}}}'

#modifie le résumé
#curl -X POST "http://192.168.50.12:3000/api/trpc/bookmarks.updateBookmark?batch=1" \
#-H "Authorization: Bearer ak1_0754a01fce6afffc9dc2_a83e5717ac99617287ba" \
#-H "Content-Type: application/json" \
#-d '{"0":{"json":{"bookmarkId":"k4tzz9wht9h6ghtjh75u3j1c","summary":"pouet"}}}'