PACKAGES="\
django-debug-toolbar \
python-memcached \
"
case $1 in
    "1.4" )
        DJANGO="https://www.djangoproject.com/download/1.4.3/tarball/"
        ;;
    "1.5" )
        DJANGO="https://www.djangoproject.com/download/1.5c1/tarball/"
        ;;
    * )
        DJANGO="django"
        ;;
esac

if [ -d env ]
then
    tar -cf env.bak.tar env
    rm -rf env
fi
virtualenv env
source env/bin/activate
pip install $DJANGO $PACKAGES
