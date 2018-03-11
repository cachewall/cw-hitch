srpm:
	shell sed -i "s/%global name[ \t].*/%global name\t\thitch/g" $(spec)
	shell grep "%global" $(spec)

	rpmbuild \
		-bs \
		--define "_srcrpmdir $(outdir)" \
		--define "_sourcedir $(CURDIR)" \
		--undefine "dist" \
		$(spec)

