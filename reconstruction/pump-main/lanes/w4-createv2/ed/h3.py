EDITS=[(" let depth=if let QuoteSource::Nested(depth)=source {depth} else {0};\n"," let depth=match source {QuoteSource::Nested(depth)=>depth,_=>0};\n")]
