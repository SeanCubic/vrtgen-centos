//% macro define_struct(struct)
/**
//% for line in struct.doc
 * ${line}
//% endfor
 */
struct ${struct.name} {
/*{% for field in struct.fields %}*/
//%     set member = field.member
    /**
     * ${field.getter.doc}.
     */
    ${field.type} ${field.getter.name}() const
    {
//%     if field.type == 'bool'
        return GET_BIT32(${member.name}, ${field.offset});
//%     elif field.bits % 8 == 0
        return ${member.name}.get();
//%     else
        return (${field.type}) vrtgen::get_int(${member.name}, ${field.offset}, ${field.bits});
//%     endif
    }

    /**
     * ${field.setter.doc}.
     */
    void ${field.setter.name}(${field.type} value)
    {
//%     if field.type == 'bool'
        SET_BIT32(${member.name}, ${field.offset}, value);
//%     elif field.bits % 8 == 0
        ${member.name}.set(value);
//%     else
        vrtgen::set_int(${member.name}, ${field.offset}, ${field.bits}, value);
//%     endif
    }

/*{% endfor %}*/
private:
/*{% for member in struct.members %}*/
    /**
//%      for line in member.doc
     * ${line}
//%      endfor
     */
    ${member.decl};
/*{%     if not loop.last %}*/

/*{%     endif %}*/
/*{% endfor %}*/
};
//% endmacro
//% set guard = '_VRTGEN_PACKING_' + name.upper() + '_HPP_'
#ifndef ${guard}
#define ${guard}

#include <vrtgen/types.hpp>
#include <vrtgen/enums.hpp>
#include <vrtgen/utils/macros.hpp>

namespace vrtgen {
    namespace packing {
/*{% for struct in structs %}*/
/*{%     if not loop.first %}*/

/*{%     endif %}*/
        ${define_struct(struct)|indent(8)}
/*{% endfor %}*/
    }
}

#endif // ${guard}
