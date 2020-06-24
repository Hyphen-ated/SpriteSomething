for f in resources/user/snes/zelda3/link/*.zspr
do    
    echo "$f"
    python SpriteSomething.py --export-showcase-gif --sprite "$f"    
done