import feedparser, datetime
 
tistory_blog_uri="https://twodragon.tistory.com"
feed = feedparser.parse(tistory_blog_uri+"/rss")
 
markdown_text = """

###  🐱 github stats  

<div id="main" align="center">
    <img src="https://github-readme-stats.vercel.app/api?username=peterica&count_private=true&show_icons=true&theme=radical"
        style="height: auto; margin-left: 20px; margin-right: 20px; padding: 10px;"/>
    <img src="https://github-readme-stats.vercel.app/api/top-langs/?username=peterica&layout=compact"   
        style="height: auto; margin-left: 20px; margin-right: 20px; padding: 10px;"/>
</div>

###  💁 About Me  
<p align="center">
    <a href="https://twodragon.tistory.com/"><img src="https://img.shields.io/badge/Blog-FF5722?style=flat-square&logo=Blogger&logoColor=white"/></a>
    <a href="https://2twodragon.com/"><img src="https://img.shields.io/badge/Blog-FF5722?style=flat-square&logo=Blogger&logoColor=white"/></a>
    <a href="mailto:twodragon114@gmail.com"><img src="https://img.shields.io/badge/Gmail-d14836?style=flat-square&logo=Gmail&logoColor=white&link=ilovefran.ofm@gmail.com"/></a>
</p>

<br>

## Recent blog posts
""" # list of blog posts will be appended here
 
for i in feed['entries']:
    dt = datetime.datetime.strptime(i['published'], "%a, %d %b %Y %H:%M:%S %z").strftime("%b %d, %Y")
    markdown_text += f"<a href =\"{i['link']}\"> {i['title']} </a> <br>"

# Save to a Markdown file
f = open("README.md",mode="w", encoding="utf-8")
f.write(markdown_text)
f.close()
