import strawberry

# Berry Tester
from service.about import ModuleAbout


@strawberry.type
class Query(
    ModuleAbout.qry
):
    pass
