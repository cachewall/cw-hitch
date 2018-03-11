name = hitch

srpm:
	shell sed -i "s/%global name[ \t].*/%global name\t\t$(name)/g" $(spec)
	shell grep "%global" $(spec)

	shell mv $(spec) $(name).spec

	rpmbuild \
		-bs \
		--define "_srcrpmdir $(outdir)" \
		--define "_sourcedir $(CURDIR)" \
		--undefine "dist" \
		$(name).spec

