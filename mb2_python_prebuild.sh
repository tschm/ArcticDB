echo "REMOVING BUILD ARTIFACTS!"
rm -rf build/
rm -f tests/cpp/test_unit_arcticcxx
rm -f tests/cpp/arcticcxx_rapidcheck_tests

rm -f arcticcxx.so
rm -f arcticcxx_toolbox.so

if [ ! -d "/opt/arcticdb" ]; then
    ln -s /workspace /opt/arcticdb
fi

cp -r /opt/arcticdb/arcticdb_link/* /opt/arcticdb
