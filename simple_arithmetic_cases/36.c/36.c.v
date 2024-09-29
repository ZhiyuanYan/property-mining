module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [10:0] c
);



    
    always @(posedge clk) begin
        if(rst)begin
            c<=0;
            // n<=32;
        end
        else begin
            if(selector&&(c !=500))begin
                c <= c + 1;
            end
            else if(selector&&(c ==500))begin
                c <= 1;
            end
        end
    end
    assert property (!((c>500)));
endmodule